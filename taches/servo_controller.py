import time
from board import SCL, SDA
import busio
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685


class ServoController:
    SAFE_ANGLES = {
        0: (50, 150),
        1: (0, 180),
        2: (70, 130),
        7: (0,  185),
    }
    MIN_PULSE = 600
    MAX_PULSE = 2400

    def __init__(self):
        i2c = busio.I2C(SCL, SDA)
        self.pca = PCA9685(i2c, address=0x5f)
        self.pca.frequency = 50
        self.servos = {
            ch: servo.Servo(
                self.pca.channels[ch],
                min_pulse=self.MIN_PULSE,
                max_pulse=self.MAX_PULSE,
                actuation_range=180,
            )
            for ch in self.SAFE_ANGLES
        }

    def set_angle(self, channel: int, angle: float):
        if channel not in self.servos:
            raise ValueError(f"Canal {channel} non disponible. Choisir parmi {list(self.SAFE_ANGLES)}")
        lo, hi = self.SAFE_ANGLES[channel]
        self.servos[channel].angle = max(lo, min(hi, angle))

    def center_all(self):
        for ch in self.SAFE_ANGLES:
            self.set_angle(ch, 90)
            time.sleep(0.1)

    def release(self):
        self.pca.deinit()