import time
import threading

import cv2
import numpy as np

import servo_controller as servo
import robot_controller as robot

try:
    from picamera2 import Picamera2
    HAS_PICAMERA2 = True
except ImportError:
    HAS_PICAMERA2 = False

try:
    from flask import Flask, Response
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


class RedLineFollowingController:
    WHEEL_CHANNEL     = 0
    HEAD_PAN_CHANNEL  = 1
    HEAD_TILT_CHANNEL = 2

    WHEEL_CENTER      = 100
    HEAD_PAN_CENTER   = 110
    HEAD_TILT_ANGLE   = 70

    ANGLE_MIN         = 50
    ANGLE_MAX         = 150
    STEERING_GAIN     = 60
    STEERING_INVERT   = True
    OFFSET_BIAS       = 0.0
    HEAD_FOLLOW_GAIN  = 15

    SPEED = 0.3

    LOWER_RED_1 = np.array([0, 100, 80])
    UPPER_RED_1 = np.array([10, 255, 255])
    LOWER_RED_2 = np.array([170, 100, 80])
    UPPER_RED_2 = np.array([180, 255, 255])
    MIN_CONTOUR_AREA = 500

    LINE_LOST_TIMEOUT = 1.2

    SEARCH_PAN_AMPLITUDE = 25
    SEARCH_PAN_SPEED     = 40
    SEARCH_SPIN_SPEED    = 0.2
    SEARCH_GIVE_UP_TIME  = 6.0

    CAMERA_SIZE = (640, 480)
    ROI_TOP_RATIO = 0.5

    def __init__(self, camera_id=0, debug_stream=False, debug_port=5000):
        self.robot   = robot.RobotController()
        self.servos  = servo.ServoController()
        self.camera_id = camera_id
        if debug_stream and not HAS_FLASK:
            print("Flask n'est pas installé, debug_stream désactivé (pip install flask)")
        self.debug_stream = debug_stream and HAS_FLASK
        self.debug_port = debug_port

        self._running = False
        self._cam = None
        self._cam_is_picamera2 = False

        self._latest_frame = None
        self._frame_lock = threading.Lock()

    def _open_camera(self):
        if HAS_PICAMERA2:
            cam = Picamera2()
            cam.configure(cam.create_preview_configuration(
                main={"size": self.CAMERA_SIZE, "format": "RGB888"}
            ))
            cam.start()
            self._cam_is_picamera2 = True
            return cam
        else:
            cam = cv2.VideoCapture(self.camera_id)
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.CAMERA_SIZE[0])
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.CAMERA_SIZE[1])
            self._cam_is_picamera2 = False
            return cam

    def _read_frame(self):
        if self._cam_is_picamera2:
            return self._cam.capture_array()
        ret, frame = self._cam.read()
        return frame if ret else None

    def _close_camera(self):
        if self._cam is None:
            return
        if self._cam_is_picamera2:
            self._cam.stop()
        else:
            self._cam.release()

    def _find_line_offset(self, frame):
        h, w = frame.shape[:2]
        roi_top = int(h * self.ROI_TOP_RATIO)
        roi = frame[roi_top:h, :]

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.LOWER_RED_1, self.UPPER_RED_1) | \
               cv2.inRange(hsv, self.LOWER_RED_2, self.UPPER_RED_2)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            return None, frame

        c = max(cnts, key=cv2.contourArea)
        if cv2.contourArea(c) < self.MIN_CONTOUR_AREA:
            return None, frame

        M = cv2.moments(c)
        if M["m00"] == 0:
            return None, frame

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        offset = (cx - (w / 2)) / (w / 2)
        offset -= self.OFFSET_BIAS

        cv2.drawContours(roi, [c], -1, (0, 255, 0), 2)
        cv2.circle(roi, (cx, cy), 6, (255, 0, 0), -1)
        frame[roi_top:h, :] = roi

        return offset, frame

    def _clamp_angle(self, angle: float) -> float:
        return max(self.ANGLE_MIN, min(self.ANGLE_MAX, angle))

    def _run_debug_server(self):
        app = Flask(__name__)

        def gen_stream():
            while self._running:
                with self._frame_lock:
                    frame = self._latest_frame
                if frame is None:
                    time.sleep(0.05)
                    continue
                ok, jpg = cv2.imencode('.jpg', frame)
                if ok:
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
                           + jpg.tobytes() + b'\r\n')

        @app.route('/')
        def index():
            return '<img src="/stream">'

        @app.route('/stream')
        def stream():
            return Response(gen_stream(),
                             mimetype='multipart/x-mixed-replace; boundary=frame')

        print(f"Serveur de debug démarré sur http://0.0.0.0:{self.debug_port}")
        try:
            app.run(host='0.0.0.0', port=self.debug_port, debug=False,
                    use_reloader=False, threaded=True)
        except Exception as e:
            print(f"Erreur serveur de debug: {e}")

    def _search_for_line(self, search_started_at):
        elapsed = time.time() - search_started_at

        sweep_period = (2 * self.SEARCH_PAN_AMPLITUDE) / self.SEARCH_PAN_SPEED * 2
        phase = (elapsed % sweep_period) / sweep_period
        if phase < 0.5:
            pan_offset = -self.SEARCH_PAN_AMPLITUDE + (4 * self.SEARCH_PAN_AMPLITUDE * phase)
        else:
            pan_offset = (3 * self.SEARCH_PAN_AMPLITUDE) - (4 * self.SEARCH_PAN_AMPLITUDE * phase)

        pan_angle = self._clamp_angle(self.HEAD_PAN_CENTER + pan_offset)
        self.servos.set_angle(self.HEAD_PAN_CHANNEL, pan_angle)

        if hasattr(self.robot, "spin"):
            self.robot.spin(self.SEARCH_SPIN_SPEED)
        elif not self.robot.moving:
            self.robot.SPEED = self.SEARCH_SPIN_SPEED
            self.robot.start()

        return elapsed > self.SEARCH_GIVE_UP_TIME

    def _follow_loop(self):
        self.servos.set_angle(self.HEAD_TILT_CHANNEL, self.HEAD_TILT_ANGLE)
        self.servos.set_angle(self.HEAD_PAN_CHANNEL, self.HEAD_PAN_CENTER)
        self.servos.set_angle(self.WHEEL_CHANNEL, self.WHEEL_CENTER)
        time.sleep(0.5)

        self._cam = self._open_camera()
        self.robot.SPEED = self.SPEED
        self.robot.start()

        line_lost_since = None
        searching = False
        search_started_at = None
        gave_up = False

        while self._running:
            frame = self._read_frame()
            if frame is None:
                continue

            offset, annotated = self._find_line_offset(frame)

            if offset is not None:
                line_lost_since = None
                if searching:
                    searching = False
                    search_started_at = None
                    gave_up = False
                    self.servos.set_angle(self.HEAD_PAN_CHANNEL, self.HEAD_PAN_CENTER)
                    self.robot.SPEED = self.SPEED

                steer_offset = -offset if self.STEERING_INVERT else offset
                angle = self.WHEEL_CENTER + steer_offset * self.STEERING_GAIN
                angle = self._clamp_angle(angle)
                self.servos.set_angle(self.WHEEL_CHANNEL, angle)

                pan_angle = self.HEAD_PAN_CENTER + steer_offset * self.HEAD_FOLLOW_GAIN
                pan_angle = self._clamp_angle(pan_angle)
                self.servos.set_angle(self.HEAD_PAN_CHANNEL, pan_angle)

                if not self.robot.moving:
                    self.robot.start()

            else:
                if line_lost_since is None:
                    line_lost_since = time.time()

                elapsed = time.time() - line_lost_since

                if elapsed > self.LINE_LOST_TIMEOUT:
                    self.servos.set_angle(self.WHEEL_CHANNEL, self.WHEEL_CENTER)

                    if not searching:
                        searching = True
                        search_started_at = time.time()

                    if not gave_up:
                        gave_up = self._search_for_line(search_started_at)
                    elif self.robot.moving:
                        self.robot.stop()

            if self.debug_stream:
                with self._frame_lock:
                    self._latest_frame = annotated

            time.sleep(0.02)

    def start(self):
        self._running = True

        if self.debug_stream:
            threading.Thread(target=self._run_debug_server, daemon=True).start()

        try:
            self._follow_loop()
        except (KeyboardInterrupt, Exception):
            pass
        finally:
            self.stop()

    def start_async(self) -> threading.Thread:
        self._running = True
        if self.debug_stream:
            threading.Thread(target=self._run_debug_server, daemon=True).start()
        t = threading.Thread(target=self._follow_loop, daemon=True)
        t.start()
        return t

    def stop(self):
        self._running = False
        self._close_camera()
        self.robot.stop()
        self.servos.set_angle(self.HEAD_PAN_CHANNEL, 90)
        self.servos.set_angle(self.WHEEL_CHANNEL, self.WHEEL_CENTER)
        time.sleep(0.2)
        self.servos.release()


def run():
    controller = RedLineFollowingController(camera_id=0, debug_stream=True)
    try:
        controller.start()
    except KeyboardInterrupt:
        controller.stop()


if __name__ == "__main__":
    run()