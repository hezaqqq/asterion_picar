#!/usr/bin/env python3
# coding: utf-8

import cv2
import numpy as np
import time
import threading
from flask import Flask, Response

from servo_controller import ServoController
from robot_controller import RobotController

HEAD_TILT_CHANNEL = 2   # tete haut/bas
HEAD_PAN_CHANNEL  = 1   # tete gauche/droite
WHEEL_CHANNEL     = 0   # direction des roues

HEAD_TILT_ANGLE   = 130  # le plus bas autorise pour ce servo (limite SAFE_ANGLES)
HEAD_PAN_CENTER   = 100  # a tester/ajuster pour que la tete soit bien droite
WHEEL_CENTER      = 100  # a tester/ajuster pour que les roues soient bien droites

STEERING_GAIN     = 25   # sensibilite du virage, augmente si le robot tourne pas assez

latest_frame = None
lock = threading.Lock()


def get_camera():
    from picamera2 import Picamera2
    cam = Picamera2()
    cam.configure(cam.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
    cam.start()
    return cam


def find_line_offset(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower1 = np.array([0, 100, 80])
    upper1 = np.array([10, 255, 255])
    lower2 = np.array([170, 100, 80])
    upper2 = np.array([180, 255, 255])

    mask = cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None, frame

    c = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(c) < 500:
        return None, frame

    M = cv2.moments(c)
    if M["m00"] == 0:
        return None, frame

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])
    w = frame.shape[1]
    offset = (cx - w / 2) / (w / 2)

    cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)
    cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)

    return offset, frame


# --------- serveur web pour voir la camera ---------
app = Flask(__name__)

def gen_stream():
    global latest_frame
    while True:
        with lock:
            if latest_frame is None:
                continue
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
# -------------------------------------------------------------------


def main():
    global latest_frame

    servos = ServoController()
    robot = RobotController()

    servos.set_angle(HEAD_TILT_CHANNEL, HEAD_TILT_ANGLE)
    servos.set_angle(HEAD_PAN_CHANNEL, HEAD_PAN_CENTER)
    servos.set_angle(WHEEL_CHANNEL, WHEEL_CENTER)
    time.sleep(1.0)

    cam = get_camera()
    robot.start()

    threading.Thread(target=run_server, daemon=True).start()

    try:
        while True:
            frame = cam.capture_array()
            if frame is None:
                continue

            offset, frame = find_line_offset(frame)

            if offset is not None:
                angle = WHEEL_CENTER + offset * STEERING_GAIN
                angle = max(60, min(140, angle))
                servos.set_angle(WHEEL_CHANNEL, angle)
            else:
                servos.set_angle(WHEEL_CHANNEL, WHEEL_CENTER)

            with lock:
                latest_frame = frame

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("stop")

    finally:
        robot.release()
        servos.set_angle(WHEEL_CHANNEL, WHEEL_CENTER)
        servos.set_angle(HEAD_PAN_CHANNEL, HEAD_PAN_CENTER)
        time.sleep(0.2)
        servos.release()
        cam.stop()


if __name__ == "__main__":
    main()