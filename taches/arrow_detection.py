import cv2
import numpy as np
import threading
import time
import robot_controller
from servo_controller import ServoController
import ultrasonic_sensor
from flask import Flask, Response
from picamera2 import Picamera2

latest_frame = None
lock = threading.Lock()


def get_camera():
    cam = Picamera2()
    cam.configure(cam.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
    cam.start()
    return cam


def read_frame(cam):
    frame_rgb = cam.capture_array()
    if frame_rgb is not None:
        return cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    return None


def detect_direction(frame):
    frame_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_blur = cv2.GaussianBlur(frame_gris, (5, 5), 0)

    # trouve les sommets
    sommets = cv2.goodFeaturesToTrack(frame_blur, 10, qualityLevel=0.1, minDistance=10)
    direction = None

    if sommets is not None:
        coords = np.int32(sommets).reshape(-1, 2)

        # dessine les coins
        for (x, y) in coords:
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

        #ligne milieu
        x_max = coords[:, 0].max()
        x_min = coords[:, 0].min()
        x_moy = int((x_max + x_min) / 2)
        
        cv2.line(frame, (x_moy, 0), (x_moy, frame.shape[0]), (0, 0, 255), 2)

        # Compte les coins
        nb_g = np.sum(coords[:, 0] < x_moy)
        nb_d = np.sum(coords[:, 0] > x_moy)
        
        # Determine direction
        if nb_g > nb_d:
            direction = "gauche"
        elif nb_d > nb_g:
            direction = "droite"
        else:
            direction = "centre"

        # dessine sur la camera
        cv2.putText(frame, f"G: {nb_g} | D: {nb_d} ({direction})", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    return direction, frame


app = Flask(__name__)
def gen_stream():
    global latest_frame
    while True:
        with lock:
            if latest_frame is None:
                continue
            # Encode the processed frame containing lines, circles, and text
            ok, jpg = cv2.imencode('.jpg', latest_frame)
        if ok:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpg.tobytes() + b'\r\n')
@app.route('/')
def index():
    return '<img src="/stream">'
@app.route('/stream')
def stream():
    return Response(gen_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')
def run_server():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


def main():
    global latest_frame
    cam = get_camera()
    history = []

    ANGLE_CENTER_ROUE = 100
    ANGLE_MIN_ROUE    = 60
    ANGLE_MAX_ROUE    = 140

    SPEED_STRAIGHT = 0.25
    SPEED_CURVE    = 0.2

    REVERSE_TIME   = 3.5
    RAMP_TIME      = 0.2

    OBSTACLE_DIST_MM = 450

    sensor    = ultrasonic_sensor.UltrasonicSensor()
    robot     = robot_controller.RobotController(sensor=sensor, auto_watch=False)
    servos    = ServoController()

    # lance le serveur
    threading.Thread(target=run_server, daemon=True).start()

    try:
        robot.SPEED = SPEED_STRAIGHT
        servos.set_angle(2, 85)
        servos.set_angle(1, 90)
        servos.set_angle(0, ANGLE_CENTER_ROUE)
        robot.start()
        while True:
            frame = read_frame(cam)
            if frame is None:
                continue

            direction, frame = detect_direction(frame)

            if direction:
                history.append(direction)
                if len(history) > 5:
                    history.pop(0)
                if sensor.get_distance_mm() <= OBSTACLE_DIST_MM:
                    if direction == "droite":
                        servos.set_angle(0, ANGLE_MIN_ROUE)
                        robot.SPEED = SPEED_CURVE
                        time.sleep(3)
                        robot.stop()
                        time.sleep(0.1)
                        robot.start()
                        servos.set_angle(0, ANGLE_MAX_ROUE)
                        robot.motors.drive(
                            -SPEED_CURVE,
                            ramp_time=REVERSE_TIME
                        )
                        robot.stop()
                        time.sleep(0.1)
                        servos.set_angle(0, ANGLE_CENTER_ROUE)
                        robot.start()

                    elif direction == "gauche":
                        servos.set_angle(0, ANGLE_MAX_ROUE)
                        robot.SPEED = SPEED_CURVE
                        time.sleep(3)
                        robot.stop()
                        time.sleep(0.1)
                        servos.set_angle(0, ANGLE_MIN_ROUE)
                        robot.start()
                        robot.motors.drive(
                            -SPEED_CURVE,
                            ramp_time=REVERSE_TIME
                        )
                        robot.stop()
                        time.sleep(0.1)
                        servos.set_angle(0, ANGLE_CENTER_ROUE)
                        robot.start()
                        


                    else:
                        servos.set_angle(0, ANGLE_CENTER_ROUE)
                        robot.SPEED = SPEED_STRAIGHT
                    
                    

            with lock:
                latest_frame = frame.copy()

    except KeyboardInterrupt:
            pass
    finally:
        robot.stop()
        robot.hazard_off()
        servos.set_angle(1, 90)
        servos.set_angle(0, ANGLE_CENTER_ROUE)


if __name__ == "__main__":
    main()