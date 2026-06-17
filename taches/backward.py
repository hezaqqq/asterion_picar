import time
import threading
import smbus

import servo_controller as servo
import robot_controller as robot


class ADS7830:
    CMD     = 0x84
    ADDRESS = 0x48

    def __init__(self):
        self.bus = smbus.SMBus(1)

    def read(self, channel: int) -> int:

        cmd = self.CMD | (((channel << 2 | channel >> 1) & 0x07) << 4)
        return self.bus.read_byte_data(self.ADDRESS, cmd)


class GyroSteeringController:
    ADC_CHANNEL   = 1
    CALIB_SAMPLES = 20
    DEAD_ZONE     = 5 
    ANGLE_STEP    = 5 
    ANGLE_CENTER  = 100
    ANGLE_MIN     = 60
    ANGLE_MAX     = 130

    def __init__(self):
        self.robot      = robot.RobotController()
        self.adc        = ADS7830()
        self.servos     = servo.ServoController()
        self._running   = False
        self._baseline  = 0
        self._thread    = None

    def _calibrate(self):
        self._baseline = sum(self.adc.read(self.ADC_CHANNEL) for _ in range(self.CALIB_SAMPLES)) / self.CALIB_SAMPLES

    def _correction_turn(self):
        current_angle  = self.ANGLE_CENTER
        was_moving     = self.robot.moving

        self.servos.set_angle(0, current_angle)

        while self._running:
            ecart = self.adc.read(self.ADC_CHANNEL) - self._baseline

            if ecart < -self.DEAD_ZONE:
                current_angle = max(self.ANGLE_MAX, current_angle - self.ANGLE_STEP)
            elif ecart > self.DEAD_ZONE:
                current_angle = min(self.ANGLE_MIN, current_angle + self.ANGLE_STEP)

            self.servos.set_angle(0, current_angle)

            if was_moving and not self.robot.moving:
                self.robot.motors.drive(-robot.RobotController.SPEED, ramp_time=2.0)
                time.sleep(1.5)
                self.robot.motors.stop(ramp_time=0.1)
                self.servos.set_angle(0, self.ANGLE_CENTER)
                time.sleep(2.0)
                self.robot.start()

            was_moving = self.robot.moving
            time.sleep(0.05)

    def start(self):
        self._calibrate()
        self._running = True
        self.robot.start()
        self._thread = threading.Thread(target=self._correction_turn, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self.servos.set_angle(0, self.ANGLE_CENTER)
        self.servos.release()
        self.robot.release()