import cv2
import numpy as np
import threading
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

def get_color_masks(hsv):
    # Blue
    blue_lower = np.array([95, 80, 50])
    blue_upper = np.array([135, 255, 255])
    mask_blue = cv2.inRange(hsv, blue_lower, blue_upper)

    # Yellow
    yellow_lower = np.array([18, 80, 80])
    yellow_upper = np.array([35, 255, 255])
    mask_yellow = cv2.inRange(hsv, yellow_lower, yellow_upper)

    # Red
    red_lower1 = np.array([0, 90, 60])
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([170, 90, 60])
    red_upper2 = np.array([180, 255, 255])
    mask_red = cv2.inRange(hsv, red_lower1, red_upper1) | cv2.inRange(hsv, red_lower2, red_upper2)

    return mask_blue, mask_yellow, mask_red


def classify_shape(cnt):
    perimeter = cv2.arcLength(cnt, True)
    if perimeter == 0:
        return None
    approx = cv2.approxPolyDP(cnt, 0.03 * perimeter, True)
    area = cv2.contourArea(cnt)
    if area < 400:
        return None

    vertices = len(approx)

    if vertices == 3:
        return "triangle"
    elif vertices == 4:
        x, y, w, h = cv2.boundingRect(approx)
        ratio = w / float(h)
        if 0.75 <= ratio <= 1.3:
            return "square"
        return None
    elif vertices > 6:
        # 4*pi*area / perimeter^2 ~ 1 for circle
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        if circularity > 0.7:
            return "circle"
        return None
    return None


def detect_signs(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask_blue, mask_yellow, mask_red = get_color_masks(hsv)

    combined_mask = mask_blue | mask_yellow | mask_red
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    sign_code = None
    sign_label = None

    for cnt in contours:
        shape = classify_shape(cnt)
        if shape is None:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        roi_mask_blue = mask_blue[y:y + h, x:x + w]
        roi_mask_yellow = mask_yellow[y:y + h, x:x + w]
        roi_mask_red = mask_red[y:y + h, x:x + w]

        blue_amount = cv2.countNonZero(roi_mask_blue)
        yellow_amount = cv2.countNonZero(roi_mask_yellow)
        red_amount = cv2.countNonZero(roi_mask_red)

        color = None
        max_amount = max(blue_amount, yellow_amount, red_amount)
        if max_amount < 50:
            continue
        if max_amount == blue_amount:
            color = "blue"
        elif max_amount == yellow_amount:
            color = "yellow"
        else:
            color = "red"

        code = None
        label = None
        if shape == "square" and color == "blue":
            code, label = 1, "Square+Blue"
        elif shape == "triangle" and color == "yellow":
            code, label = 2, "Triangle+Yellow"
        elif shape == "circle" and color == "red":
            code, label = 3, "Circle+Red"

        if code is not None:
            sign_code = code
            sign_label = label

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"{label} ({code})", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

    if sign_code is not None:
        cv2.putText(frame, f"Sign code: {sign_code}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    return sign_code, frame


# ======================================SERVER CAMERA======================================================#
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
# ========================================================================================================#

def main():
    global latest_frame
    cam = get_camera()
    history = []

    threading.Thread(target=run_server, daemon=True).start()

    try:
        while True:
            frame = read_frame(cam)
            if frame is None:
                continue

            code, frame = detect_signs(frame)

            if code is not None:
                history.append(code)
                if len(history) > 5:
                    history.pop(0)

                stable = code if history.count(code) >= 3 else None

            with lock:
                latest_frame = frame.copy()

    except KeyboardInterrupt:
        print("\nStop")

    finally:
        cam.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()