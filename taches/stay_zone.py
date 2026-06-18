import line_reading as line_reading
import robot_controller as robot
import servo_controller as servo
import time

class StayInZone:

    ANGLE_CENTER_ROUE = 100
    ANGLE_MIN_ROUE    = 60
    ANGLE_MAX_ROUE    = 140

    SPEED_STRAIGHT = 0.35
    SPEED_CURVE    = 0.30

    REVERSE_TIME   = 1.5   # durée du recul (s)
    RAMP_TIME      = 0.2   # durée de la rampe moteur (s)

    def __init__(self):
        self.robot  = robot.RobotController()
        self.line   = line_reading.LineReading()
        self.servos = servo.ServoController()
        self._running = False

    def _reverse(self, steer_angle: float):
        self.robot.stop()
        self.servos.set_angle(0, steer_angle)
        time.sleep(0.1)

        self.robot.motors.drive(-self.SPEED_CURVE, ramp_time=self.RAMP_TIME)
        time.sleep(self.REVERSE_TIME)

        self.robot.stop()
        time.sleep(0.1)
        self.servos.set_angle(0, self.ANGLE_CENTER_ROUE)
        self.robot.SPEED = self.SPEED_STRAIGHT
        self.robot.start()

    def _follow_zone(self):
        self.servos.set_angle(0, self.ANGLE_CENTER_ROUE)
        self.robot.SPEED = self.SPEED_STRAIGHT
        self.robot.start()

        while self._running:
            l, m, r = self.line.line_read()

            if r == 1 and m == 0 and l == 0:
                self._reverse(self.ANGLE_MAX_ROUE)

            elif r == 1 and m == 1 and l == 0:
                self._reverse(self.ANGLE_MAX_ROUE)

            elif r == 0 and m == 0 and l == 1:
                self._reverse(self.ANGLE_MIN_ROUE)

            elif r == 0 and m == 1 and l == 1:
                self._reverse(self.ANGLE_MIN_ROUE)

            elif r == 1 and m == 1 and l == 1:  
                self._reverse(self.ANGLE_CENTER_ROUE)

            # else on avance
            time.sleep(0.05)

    def run(self):
        self._running = True
        try:
            self._follow_zone()
        except KeyboardInterrupt:
            pass
        finally:
            self.robot.stop()
            self.robot.hazard_off()

if __name__ == "__main__":
    stay_in_zone = StayInZone()
    stay_in_zone.run()