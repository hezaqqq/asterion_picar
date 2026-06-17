import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import motor

class MotorController:
    # Servo de direction (canal 0)
    SERVO_CHANNEL = 0
    SERVO_LEFT    = 3277
    SERVO_CENTER  = 4915
    SERVO_RIGHT   = 6554

    # Canaux moteurs
    _MOTOR_PINS = [
        (15, 14),   # M1
        (12, 13),   # M2
        (11, 10),   # M3
        (8,  9),    # M4
    ]

    def __init__(self):
        self.i2c = busio.I2C(SCL, SDA)
        self.pca = PCA9685(self.i2c, address=0x5f)
        self.pca.frequency = 1000

        self.motors = [
            motor.DCMotor(self.pca.channels[a], self.pca.channels[b])
            for a, b in self._MOTOR_PINS
        ]
        for m in self.motors:
            m.decay_mode = motor.SLOW_DECAY

        self.current_throttle = 0.0

    def drive(self, throttle: float, ramp_time: float = 1.0):
        throttle = max(-1.0, min(1.0, throttle))
        steps = 100
        delay = ramp_time / steps
        for step in range(1, steps + 1):
            t = self.current_throttle + (throttle - self.current_throttle) * step / steps
            for m in self.motors:
                m.throttle = t
            time.sleep(delay)
        self.current_throttle = throttle

    def stop(self, ramp_time: float = 0.3):
        self.drive(0.0, ramp_time=ramp_time)

    def release(self):
        for m in self.motors:
            m.throttle = 0
        self.pca.deinit()