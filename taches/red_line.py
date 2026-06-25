import cv2
import numpy as np
import threading
import time
import robot_controller
from servo_controller import ServoController
import ultrasonic_sensor

# =========================
# CONSTANTES
# =========================

CAMERA_ID = 0

# Servo direction (roues)
STEERING_CHANNEL = 1
CENTER_STEERING = 90

# Servo tête verticale
HEAD_TILT_CHANNEL = 2
HEAD_TILT_ANGLE = 130  # à ajuster selon ton montage

# Vitesse du robot
BASE_SPEED = 0.3

# =========================
# INITIALISATION
# =========================



cap = cv2.VideoCapture(CAMERA_ID)

servos.set_angle(HEAD_TILT_CHANNEL, HEAD_TILT_ANGLE)
servos.set_angle(STEERING_CHANNEL, CENTER_STEERING)

# =========================
# BOUCLE PRINCIPALE
# =========================

while True:

    ret, frame = cap.read()

    if not ret:
        continue

    h, w = frame.shape[:2]

    roi = frame[int(h * 0.6):h, :]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 150, 150])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([170, 150, 150])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    mask_red = cv2.bitwise_or(mask1, mask2)

    kernel = np.ones((5, 5), np.uint8)

    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, kernel)

    points = []

    h_mask, w_mask = mask_red.shape

    for x in range(w_mask):
        ys = np.where(mask_red[:, x] > 0)[0]

        if len(ys) > 0:
            cy = int(np.mean(ys))
            points.append((x, cy))

    for i in range(1, len(points)):
        cv2.line(roi, points[i - 1], points[i], (0, 255, 0), 2)

    if len(points) > 20:

        target_index = int(len(points) * 0.25)

        target_x = points[target_index][0]

        center_x = w_mask // 2

        error = target_x - center_x

        steering = np.clip(error * 0.15, -30, 30)

        direction_angle = CENTER_STEERING + steering

        servos.set_angle(
            STEERING_CHANNEL,
            int(direction_angle)
        )

        motors.forward(BASE_SPEED)

        cv2.circle(
            roi,
            (target_x, points[target_index][1]),
            8,
            (255, 0, 0),
            -1
        )

    else:
        motors.stop()

    cv2.imshow("Line Following", frame)
    cv2.imshow("Red Mask", mask_red)

    if cv2.waitKey(1) & 0xFF == 27:
        break

# =========================
# FIN
# =========================

motors.stop()
servos.set_angle(STEERING_CHANNEL, CENTER_STEERING)

cap.release()
cv2.destroyAllWindows()