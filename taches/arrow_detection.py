#!/usr/bin/env python3
# coding: utf-8

import cv2
import numpy as np

# True = webcam pour test, False = camera du robot
USE_ORDINATEUR_CAMERA = False

ARROW_REF = np.array([
    [0, 30], [60, 30], [60, 10], [100, 50], [60, 90], [60, 70], [0, 70]
], dtype=np.int32).reshape(-1, 1, 2)


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
    best_score = 0.15  # plus bas = plus strict, donc moins de fausses detections

    for c in cnts:
        area = cv2.contourArea(c)
        if area < 0.005 * w * h:
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) < 6 or len(approx) > 9:
            continue

        score = cv2.matchShapes(c, ARROW_REF, cv2.CONTOURS_MATCH_I1, 0)
        if score < best_score:
            best_score = score
            best = c

    if best is None:
        return None, frame

    c = best
    M = cv2.moments(c)
    if M["m00"] == 0:
        return None, frame
    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])

    # pointe = point du contour complet le plus loin du centre
    pts = c.reshape(-1, 2)
    dists = np.linalg.norm(pts - [cx, cy], axis=1)
    tip = pts[np.argmax(dists)]

    direction = "droite" if tip[0] > cx else "gauche"

    cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)
    cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)
    cv2.circle(frame, tuple(tip), 6, (0, 0, 255), -1)
    cv2.putText(frame, direction, (cx - 30, cy - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    return direction, frame


def main():
    cam = get_camera()
    history = []

    while True:
        frame = read_frame(cam)
        if frame is None:
            continue

        direction, frame = detect_direction(frame)

        # lisse la detection: il faut le meme resultat plusieurs fois de suite
        history.append(direction)
        if len(history) > 5:
            history.pop(0)
        stable = direction if history.count(direction) >= 4 else None

        if stable:
            print(stable)

        cv2.imshow("Arrow Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    if USE_ORDINATEUR_CAMERA:
        cam.release()
    else:
        cam.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()