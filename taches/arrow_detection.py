#!/usr/bin/env python3
# coding: utf-8

import cv2
import numpy as np
import threading
from flask import Flask, Response

# True = webcam pour test, False = camera du robot
USE_ORDINATEUR_CAMERA = False

ARROW_REF = np.array([
    [0, 30], [60, 30], [60, 10], [100, 50], [60, 90], [60, 70], [0, 70]
], dtype=np.int32).reshape(-1, 1, 2)

latest_frame = None
lock = threading.Lock()


def get_camera():
    if USE_ORDINATEUR_CAMERA:
        return cv2.VideoCapture(0)
    else:
        from picamera2 import Picamera2
        cam = Picamera2()
        cam.configure(cam.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
        cam.start()
        return cam


def read_frame(cam):
    if USE_ORDINATEUR_CAMERA:
        ok, frame = cam.read()
        return frame if ok else None
    else:
        return cam.capture_array()


#!/usr/bin/env python3
# coding: utf-8

import cv2
import numpy as np
import threading
from flask import Flask, Response

# True = webcam pour test, False = camera du robot
USE_ORDINATEUR_CAMERA = False

ARROW_REF = np.array([
    [0, 30], [60, 30], [60, 10], [100, 50], [60, 90], [60, 70], [0, 70]
], dtype=np.int32).reshape(-1, 1, 2)

latest_frame = None
lock = threading.Lock()


def get_camera():
    if USE_ORDINATEUR_CAMERA:
        return cv2.VideoCapture(0)
    else:
        from picamera2 import Picamera2
        cam = Picamera2()
        cam.configure(cam.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
        cam.start()
        return cam


def read_frame(cam):
    if USE_ORDINATEUR_CAMERA:
        ok, frame = cam.read()
        return frame if ok else None
    else:
        return cam.capture_array()


def detect_direction(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)

    cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None, frame

    h, w = frame.shape[:2]
    best = None
    best_ratio = 2.5  # plus haut = plus strict sur la forme "pointue d'un cote"

    for c in cnts:
        area = cv2.contourArea(c)
        if area < 0.01 * w * h:
            continue

        x, y, rw, rh = cv2.boundingRect(c)
        if rw < 10 or rh < 10:
            continue

        mask = np.zeros((rh, rw), dtype=np.uint8)
        cv2.drawContours(mask, [c], -1, 255, -1, offset=(-x, -y))

        col_sums = mask.sum(axis=0) / 255.0  # hauteur de matiere par colonne

        edge = max(3, rw // 8)
        left_avg = col_sums[:edge].mean()
        right_avg = col_sums[-edge:].mean()

        small = min(left_avg, right_avg)
        big = max(left_avg, right_avg)
        ratio = big / (small + 1e-5)

        if ratio > best_ratio:
            best_ratio = ratio
            best = (c, left_avg, right_avg, x, y, rw, rh)

    if best is None:
        return None, frame

    c, left_avg, right_avg, x, y, rw, rh = best

    # le cote le plus fin est la pointe de la fleche
    direction = "droite" if right_avg < left_avg else "gauche"

    M = cv2.moments(c)
    if M["m00"] == 0:
        return None, frame
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])

    cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)
    cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)
    cv2.putText(frame, direction, (cx - 30, cy - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    return direction, frame


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


def main():
    global latest_frame
    cam = get_camera()
    history = []

    if not USE_ORDINATEUR_CAMERA:
        threading.Thread(target=run_server, daemon=True).start()

    try:
        while True:
            frame = read_frame(cam)
            if frame is None:
                continue

            direction, frame = detect_direction(frame)

            history.append(direction)
            if len(history) > 5:
                history.pop(0)
            stable = direction if history.count(direction) >= 3 else None

            if stable:
                print(stable)

            if USE_ORDINATEUR_CAMERA:
                cv2.imshow("Arrow Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                with lock:
                    latest_frame = frame

    except KeyboardInterrupt:
        print("Arret demande.")

    finally:
        if USE_ORDINATEUR_CAMERA:
            cam.release()
        else:
            cam.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()


app = Flask(__name__)

def gen_stream():
    global latest_frame
    while True:
        with lock:
            if latest_frame is None:
                continue
            gray = cv2.cvtColor(latest_frame, cv2.COLOR_BGR2GRAY)
            _, dbg = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
            ok, jpg = cv2.imencode('.jpg', dbg)

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

    if not USE_ORDINATEUR_CAMERA:
        threading.Thread(target=run_server, daemon=True).start()

    try:
        while True:
            frame = read_frame(cam)
            if frame is None:
                continue

            direction, frame = detect_direction(frame)

            history.append(direction)
            if len(history) > 5:
                history.pop(0)
            stable = direction if history.count(direction) >= 3 else None

            if stable:
                print(stable)

            if USE_ORDINATEUR_CAMERA:
                cv2.imshow("Arrow Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                with lock:
                    latest_frame = frame

    except KeyboardInterrupt:
        print("Arret demande.")

    finally:
        if USE_ORDINATEUR_CAMERA:
            cam.release()
        else:
            cam.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()