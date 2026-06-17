import time
import threading

import servo_controller as servo
import line_reading as line_reading
import robot_controller as robot


class LineFollowingController:
    ANGLE_CENTER = 100
    ANGLE_MIN    = 60
    ANGLE_MAX    = 140
    HOLE_TIMEOUT = 0.5   # durée max d'un trou blanc à ignorer (s)

    SPEED_STRAIGHT = 0.40
    SPEED_CURVE    = 0.30
    SPEED_SLIGHT   = 0.35

    def __init__(self):
        self.robot   = robot.RobotController()
        self.line    = line_reading.LineReading()
        self.servos  = servo.ServoController()
        self._running = False

    def _clamp(self, angle: float) -> float:
        return max(self.ANGLE_MIN, min(self.ANGLE_MAX, angle))

    def _follow_loop(self):
        current_angle   = self.ANGLE_CENTER
        was_moving      = self.robot.moving
        hole_start      = None
        angle_pre_hole  = self.ANGLE_CENTER

        self.servos.set_angle(0, current_angle)
        self.robot.SPEED = self.SPEED_STRAIGHT
        self.robot.start()

        while self._running:
            l, m, r = self.line.read()

            if r == 0 and m == 1 and l == 0:
                current_angle = self.ANGLE_CENTER
                self.robot.SPEED = self.SPEED_STRAIGHT
                hole_start = None

            elif r == 1 and m == 0 and l == 0:
                current_angle += 20
                self.robot.SPEED = self.SPEED_CURVE
                hole_start = None

            elif r == 0 and m == 0 and l == 1:
                current_angle -= 20
                self.robot.SPEED = self.SPEED_CURVE
                hole_start = None

            elif r == 1 and m == 1 and l == 0:
                current_angle += 10
                self.robot.SPEED = self.SPEED_SLIGHT
                hole_start = None

            elif r == 0 and m == 1 and l == 1:
                current_angle -= 10
                self.robot.SPEED = self.SPEED_SLIGHT
                hole_start = None

            elif r == 1 and m == 1 and l == 1:
                current_angle = self.ANGLE_CENTER
                hole_start = None

            elif r == 0 and m == 0 and l == 0:
                if hole_start is None:
                    hole_start     = time.time()
                    angle_pre_hole = current_angle

                elapsed = time.time() - hole_start

                if elapsed > self.HOLE_TIMEOUT:
                    recoil_angle = self.ANGLE_CENTER + (self.ANGLE_CENTER - angle_pre_hole)
                    current_angle = self._clamp(recoil_angle)

                    if self.robot.moving:
                        self.robot.stop()
                        self.servos.set_angle(0, current_angle)
                        self.robot.motors.drive(
                            -self.robot.SPEED,
                            ramp_time=elapsed + 0.5,
                        )

                    hole_start    = None
                    current_angle = angle_pre_hole

            if was_moving and not self.robot.moving:
                if l or m or r:
                    time.sleep(2.0)
                    self.robot.start()

            was_moving = self.robot.moving

            current_angle = self._clamp(current_angle)
            self.servos.set_angle(0, current_angle)
            time.sleep(0.05)

    def start(self):
        self._running = True
        try:
            self._follow_loop()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def start_async(self) -> threading.Thread:
        self._running = True
        t = threading.Thread(target=self._follow_loop, daemon=True)
        t.start()
        return t

    def stop(self):
        self._running = False
        self.servos.set_angle(0, self.ANGLE_CENTER)
        self.servos.release()
        self.robot.release()