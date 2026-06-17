import line_reading as line_reading
import robot_controller as robot
import servo_controller as servo
import time

class StayInZone:

    ANGLE_CENTER_ROUE = 100
    ANGLE_MIN_ROUE    = 60
    ANGLE_MAX_ROUE    = 140

    SPEED_STRAIGHT = 0.25
    SPEED_CURVE    = 0.20
    SPEED_SLIGHT   = 0.15

    REVERSE_TIME   = 1.5

    def __init__(self):
        self.robot  = robot.RobotController()
        self.line   = line_reading.LineReading()
        self.servos = servo.ServoController()
        self._running = False

    def _follow_zone(self):
        self.servos.set_angle(0, self.ANGLE_CENTER_ROUE) 
        self.robot.SPEED = self.SPEED_STRAIGHT
        self.robot.start()

        while self._running:
            l, m, r = self.line.line_read()

            if (r == 1 and m == 0 and l == 0) or (r == 1 and m == 1 and l == 0):
                self.servos.set_angle(0, self.ANGLE_MIN_ROUE)
                self.robot.stop()
                self.robot.motors.drive(-self.SPEED_CURVE, ramp_time=0.2)
                time.sleep(self.REVERSE_TIME)
                self.robot.stop()
                self.servos.set_angle(0, self.ANGLE_CENTER_ROUE)
                self.robot.SPEED = self.SPEED_STRAIGHT
                self.robot.start()

            elif (r == 0 and m == 0 and l == 1) or (r == 0 and m == 1 and l == 1):
                self.servos.set_angle(0, self.ANGLE_MAX_ROUE)
                self.robot.stop()
                self.robot.motors.drive(-self.SPEED_CURVE, ramp_time=0.2)
                time.sleep(self.REVERSE_TIME)
                self.robot.stop()
                self.servos.set_angle(0, self.ANGLE_CENTER_ROUE)
                self.robot.SPEED = self.SPEED_STRAIGHT
                self.robot.start()

            else:
                self.robot.motors.drive(self.SPEED_STRAIGHT, ramp_time=0.1)

            time.sleep(0.05)

    def run(self):
        self._running = True
        self._follow_zone()

if __name__ == "__main__":
    stay_in_zone = StayInZone()
    try:
        stay_in_zone.run()
    except KeyboardInterrupt:
        stay_in_zone.robot.stop()
        stay_in_zone.robot.hazard_off()