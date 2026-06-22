import time
import threading

import servo_controller as servo
import line_reading as line_reading
import robot_controller as robot
from led_controller import RobotLEDController  


class LineFollowingController:
    ANGLE_CENTER   = 100
    ANGLE_MIN      = 60
    ANGLE_MAX      = 140
    HOLE_TIMEOUT   = 1   

    SPEED_STRAIGHT = 0.35
    SPEED_CURVE    = 0.30
    SPEED_SLIGHT   = 0.325

    def __init__(self):
        self.robot    = robot.RobotController()
        self.line     = line_reading.LineReading()
        self.servos   = servo.ServoController()
        self.leds     = RobotLEDController()
        self.leds.setup()
        self._running = False

    def _set_leds_state(self, state: str):
        self.leds.all_off()
        
        if state == "left":
            self.leds.led_on(5)
            self.leds.led_on(6)
        elif state == "right":
            self.leds.led_on(7)
            self.leds.led_on(8)
        elif state == "straight":
            self.leds.led_on(5)
            self.leds.led_on(6)
            self.leds.led_on(7)
            self.leds.led_on(8)
        elif state == "hole_timeout":
            self.leds.led_on(6)
            self.leds.led_on(7)
        elif state == "lost":
            self.leds.led_on(5)
            self.leds.led_on(8)

    def _clamp(self, angle: float) -> float:
        return max(self.ANGLE_MIN, min(self.ANGLE_MAX, angle))

    def _follow_loop(self):
        current_angle  = self.ANGLE_CENTER
        was_moving     = self.robot.moving
        hole_start     = None
        angle_pre_hole = self.ANGLE_CENTER
        in_hole_timeout = False 

        self.servos.set_angle(0, current_angle)
        self.robot.SPEED = self.SPEED_STRAIGHT
        self.robot.start()

        while self._running:
            l, m, r = self.line.line_read()

            if r == 0 and m == 1 and l == 0:
                current_angle    = self.ANGLE_CENTER
                self.robot.SPEED = self.SPEED_STRAIGHT
                hole_start       = None
                in_hole_timeout  = False
                self._set_leds_state("straight")

            elif r == 1 and m == 0 and l == 0:
                current_angle   += 13
                self.robot.SPEED = self.SPEED_CURVE
                hole_start       = None
                in_hole_timeout  = False
                self._set_leds_state("right")

            elif r == 0 and m == 0 and l == 1:
                current_angle   -= 13
                self.robot.SPEED = self.SPEED_CURVE
                hole_start       = None
                in_hole_timeout  = False
                self._set_leds_state("left")

            elif r == 1 and m == 1 and l == 0:
                current_angle   += 5
                self.robot.SPEED = self.SPEED_SLIGHT
                hole_start       = None
                in_hole_timeout  = False
                self._set_leds_state("right")

            elif r == 0 and m == 1 and l == 1:
                current_angle   -= 5
                self.robot.SPEED = self.SPEED_SLIGHT
                hole_start       = None
                in_hole_timeout  = False
                self._set_leds_state("left")

            elif r == 1 and m == 1 and l == 1:
                current_angle    = self.ANGLE_CENTER
                hole_start       = None
                in_hole_timeout  = False
                self._set_leds_state("straight")

            elif r == 0 and m == 0 and l == 0:
                if hole_start is None:
                    block_start    = time.time()
                    angle_pre_hole = current_angle

                elapsed = time.time() - hole_start

                if elapsed <= self.HOLE_TIMEOUT:
                    in_hole_timeout = True
                    self._set_leds_state("hole_timeout")

                else:
                    in_hole_timeout = False
                    self._set_leds_state("lost")
                    
                    recoil_angle  = self.ANGLE_CENTER + (self.ANGLE_CENTER - angle_pre_hole)
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
                    self.servos.set_angle(0, current_angle)
                    self.robot.start()

            else:
                hole_start = None
                in_hole_timeout = False

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
        self.leds.all_off()


if __name__ == "__main__":
    try:
        controller = LineFollowingController()
        controller.start()
    except KeyboardInterrupt:
        controller.robot.stop()
        controller.robot.hazard_off()
        controller.leds.all_off()