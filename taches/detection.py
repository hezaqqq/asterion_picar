# detection.py

import robot_controller as robot_controller
import ultrasonic_sensor as ultrasonic_sensor
import servo_controller as servo
import time

ANGLE_CENTER_ROUE    = 100
ANGLE_CENTER_TETE_GD = 108
ANGLE_MIN_TETE_GD    = 18
ANGLE_MAX_TETE_GD    = 198

class detection:

    def __init__(self, robot=None, servos=None, sensor=None):
        self.sensor  = sensor  or ultrasonic_sensor.UltrasonicSensor()
        self.robot   = robot   or robot_controller.RobotController(sensor=self.sensor)
        self.servos  = servos  or servo.ServoController()
        self._running = False

    def run(self):
        self.servos.set_angle(1, ANGLE_CENTER_TETE_GD)
        self.servos.set_angle(2, 75)
        self.servos.set_angle(0, ANGLE_CENTER_ROUE)
        self.robot.start()

        gauche        = True
        angle_tete_gd = ANGLE_CENTER_TETE_GD
        around        = False
        self._running = True

        try:
            while self._running:
                if gauche:
                    angle_tete_gd += 10
                    if angle_tete_gd >= ANGLE_MAX_TETE_GD:
                        gauche = False
                else:
                    angle_tete_gd -= 10
                    if angle_tete_gd <= ANGLE_MIN_TETE_GD:
                        gauche = True

                if self.sensor.get_distance_mm() < 150 and not around:
                    around = True
                    if ANGLE_MIN_TETE_GD <= angle_tete_gd <= ANGLE_CENTER_TETE_GD:
                        self.servos.set_angle(0, ANGLE_CENTER_ROUE + 30)
                        time.sleep(3)
                        self.servos.set_angle(0, ANGLE_CENTER_ROUE - 30)
                        time.sleep(3)
                    else:
                        self.servos.set_angle(0, ANGLE_CENTER_ROUE - 30)
                        time.sleep(3)
                        self.servos.set_angle(0, ANGLE_CENTER_ROUE + 30)
                        time.sleep(3)
                    self.servos.set_angle(0, ANGLE_CENTER_ROUE)
                    around = False

                self.servos.set_angle(1, angle_tete_gd)
                time.sleep(0.05)

        except KeyboardInterrupt:
            pass
        finally:
            self.robot.stop()
            self.robot.hazard_off()
            self.servos.set_angle(1, ANGLE_CENTER_TETE_GD)

if __name__ == "__main__":
    detection().run()