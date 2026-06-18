import time
import threading

import servo_controller as servo
import line_reading as line_reading
import robot_controller as robot


class LineFollowingController:
    ANGLE_CENTER   = 100
    ANGLE_MIN      = 60
    ANGLE_MAX      = 140
    HOLE_TIMEOUT   = 0.75   # durée max d'un trou blanc à ignorer (s)

    SPEED_STRAIGHT = 0.35
    SPEED_CURVE    = 0.30
    SPEED_SLIGHT   = 0.32

    def __init__(self):
        self.robot    = robot.RobotController()
        self.line     = line_reading.LineReading()
        self.servos   = servo.ServoController()
        self._running = False

    def _clamp(self, angle: float) -> float:
        return max(self.ANGLE_MIN, min(self.ANGLE_MAX, angle))

    def _follow_loop(self):
        current_angle  = self.ANGLE_CENTER
        was_moving     = self.robot.moving
        hole_start     = None
        angle_pre_hole = self.ANGLE_CENTER

        self.servos.set_angle(0, current_angle)
        self.robot.SPEED = self.SPEED_STRAIGHT
        self.robot.start()

        while self._running:
            l, m, r = self.line.line_read()

            if r == 0 and m == 1 and l == 0:           # ligne centrée
                current_angle    = self.ANGLE_CENTER
                self.robot.SPEED = self.SPEED_STRAIGHT
                hole_start       = None

            elif r == 1 and m == 0 and l == 0:         # ligne à droite → virer à droite
                current_angle   += 10
                self.robot.SPEED = self.SPEED_CURVE
                hole_start       = None

            elif r == 0 and m == 0 and l == 1:         # ligne à gauche → virer à gauche
                current_angle   -= 10
                self.robot.SPEED = self.SPEED_CURVE
                hole_start       = None

            elif r == 1 and m == 1 and l == 0:         # légèrement à droite
                current_angle   += 5
                self.robot.SPEED = self.SPEED_SLIGHT
                hole_start       = None

            elif r == 0 and m == 1 and l == 1:         # légèrement à gauche
                current_angle   -= 5
                self.robot.SPEED = self.SPEED_SLIGHT
                hole_start       = None

            elif r == 1 and m == 1 and l == 1:         # tous détecteurs actifs → tout droit
                current_angle    = self.ANGLE_CENTER
                hole_start       = None

            elif r == 0 and m == 0 and l == 0:         # ligne perdue / trou blanc
                if hole_start is None:
                    hole_start     = time.time()
                    angle_pre_hole = current_angle

                elapsed = time.time() - hole_start

                if elapsed <= self.HOLE_TIMEOUT:
                    # Trou blanc donc on continue sans rien changer
                    pass

                else:
                    # Ligne vraiment perdue → recul symétrique
                    recoil_angle  = self.ANGLE_CENTER + (self.ANGLE_CENTER - angle_pre_hole)
                    current_angle = self._clamp(recoil_angle)

                    if self.robot.moving:
                        self.robot.stop()
                        self.servos.set_angle(0, current_angle)
                        self.robot.motors.drive(
                            -self.robot.SPEED,
                            ramp_time=elapsed + 0.5,
                        )

                    # Reset et reprise comme dans le premier code
                    hole_start    = None
                    current_angle = angle_pre_hole      # reprend l'angle d'avant
                    self.servos.set_angle(0, current_angle)
                    self.robot.start()

            else:
                hole_start = None

            current_angle = self._clamp(current_angle)
            self.servos.set_angle(0, current_angle)

            if was_moving and not self.robot.moving:
                if r != 0 or m != 0 or l != 0:
                    print("Obstacle détecté — reprise dans 2s")
                    time.sleep(2.0)
                    self.robot.start()

            was_moving = self.robot.moving
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
        self.robot.stop()
        self.robot.hazard_off()


if __name__ == "__main__":
    try:
        controller = LineFollowingController()
        controller.start()
    except KeyboardInterrupt:
        controller.robot.stop()
        controller.robot.hazard_off()