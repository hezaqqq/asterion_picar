import line_reading as line_reading
import robot_controller as robot_module
import servo_controller as servo_module
import ultrasonic_sensor as ultrasonic_module
import time

class StayInZone:

    ANGLE_CENTER_ROUE = 100
    ANGLE_MIN_ROUE    = 75
    ANGLE_MAX_ROUE    = 135

    ANGLE_CENTER_TETE_GD = 90
    ANGLE_MIN_TETE_GD    = 18
    ANGLE_MAX_TETE_GD    = 162

    SPEED_STRAIGHT = 0.15
    SPEED_CURVE    = 0.2

    REVERSE_TIME   = 2.25
    RAMP_TIME      = 0.2

    OBSTACLE_DIST_MM = 275

    SLEEP_CENTRE1 = 2.5
    SLEEP_CENTRE2 = 2.5
    SLEEP_EXT1 = 2.5
    SLEEP_EXT2 = 2.5

    def __init__(self):
        self.sensor    = ultrasonic_module.UltrasonicSensor()
        self.robot     = robot_module.RobotController(sensor=self.sensor, auto_watch=False)
        self.line      = line_reading.LineReading()
        self.servos    = servo_module.ServoController()
        self._running  = False
        self._last_side = self.ANGLE_MAX_ROUE

        self._gauche        = True
        self._angle_tete_gd = 66

    # ── Ligne ──────────────────────────────────────────────────────────
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

    def _check_line(self) -> bool:
        """Retourne True si une action de recul a été déclenchée (ligne détectée)."""
        l, m, r = self.line.line_read()

        if (r == 1 and m == 0 and l == 0) or (r == 1 and m == 1 and l == 0):
            self._last_side = self.ANGLE_MAX_ROUE
            self._reverse(self.ANGLE_MAX_ROUE)
            return True

        elif (r == 0 and m == 0 and l == 1) or (r == 0 and m == 1 and l == 1):
            self._last_side = self.ANGLE_MIN_ROUE
            self._reverse(self.ANGLE_MIN_ROUE)
            return True

        elif r == 1 and m == 1 and l == 1:
            opposite = self.ANGLE_MIN_ROUE if self._last_side == self.ANGLE_MAX_ROUE else self.ANGLE_MAX_ROUE
            self._reverse(opposite)
            return True

        return False

    # ── Tête + obstacle ───────────────────────────────────────────────
    def _sweep_head(self):
        if self._gauche:
            self._angle_tete_gd += 48
            if self._angle_tete_gd >= self.ANGLE_MAX_TETE_GD:
                self._gauche = False
        else:
            self._angle_tete_gd -= 48
            if self._angle_tete_gd <= self.ANGLE_MIN_TETE_GD:
                self._gauche = True
        self.servos.set_angle(1, self._angle_tete_gd)
        time.sleep(0.15)

    def _check_obstacle(self) -> bool:
        if self.sensor.get_distance_mm() >= self.OBSTACLE_DIST_MM:
            return False

        if not self.robot.moving:
            self.robot.start(self.SPEED_CURVE)

        if self._angle_tete_gd == 18:
            # Gauche extrême → contourne par la droite, en avançant
            self.robot.stop()
            time.sleep(0.05)
            self.robot.start(-self.SPEED_CURVE)
            time.sleep(0.2)
            self.robot.stop()
            time.sleep(0.05)
            self.servos.set_angle(0, 140)
            self.robot.start(self.SPEED_CURVE)
            time.sleep(self.SLEEP_EXT1)
            self.servos.set_angle(0, 60)
            time.sleep(self.SLEEP_EXT2)
            self._angle_tete_gd = 114

        elif self._angle_tete_gd == 162:
            # Droite extrême → contourne par la gauche, en avançant
            self.robot.stop()
            time.sleep(0.05)
            self.robot.start(-self.SPEED_CURVE)
            time.sleep(0.2)
            self.robot.stop()
            time.sleep(0.05)
            self.servos.set_angle(0, 60)
            self.robot.start(self.SPEED_CURVE)
            time.sleep(self.SLEEP_EXT1)
            self.servos.set_angle(0, 140)
            time.sleep(self.SLEEP_EXT2)
            self._angle_tete_gd = 66

        elif self._angle_tete_gd == 66:
            # Centre-gauche → recul, roues à gauche, puis avance
            self.robot.stop()
            time.sleep(0.05)
            self.robot.start(-self.SPEED_CURVE)
            time.sleep(0.2)
            self.robot.stop()
            time.sleep(0.05)
            self.servos.set_angle(0, 140)
            self.robot.start(self.SPEED_CURVE)
            time.sleep(self.SLEEP_CENTRE1)
            self.servos.set_angle(0, 60)
            time.sleep(self.SLEEP_CENTRE2)
            self._angle_tete_gd = 114

        else:
            # Centre-droite → recul, roues à droite, puis avance
            self.robot.stop()
            time.sleep(0.05)
            self.robot.start(-self.SPEED_CURVE)
            time.sleep(0.2)
            self.robot.stop()
            time.sleep(0.05)
            self.servos.set_angle(0, 60)
            self.robot.start(self.SPEED_CURVE)
            time.sleep(self.SLEEP_CENTRE1)
            self.servos.set_angle(0, 140)
            time.sleep(self.SLEEP_CENTRE2)
            self._angle_tete_gd = 66

        self.servos.set_angle(0, self.ANGLE_CENTER_ROUE)
        if not self.robot.moving:
            self.robot.start(self.SPEED_STRAIGHT)
        return True

    # ── Boucle principale ────────────────────────────────────────────
    def run(self):
        self.servos.set_angle(0, self.ANGLE_CENTER_ROUE)
        self.servos.set_angle(1, 54)
        self.servos.set_angle(2, 90)
        self.robot.start(self.SPEED_STRAIGHT)

        self._running = True
        try:
            while self._running:
                # Priorité 1 : rester dans la zone (la ligne prime sur l'obstacle)
                if self._check_line():
                    self._sweep_head()
                    time.sleep(0.05)
                    continue

                # Priorité 2 : éviter un obstacle
                if self._check_obstacle():
                    self._sweep_head()
                    time.sleep(0.05)
                    continue

                # Rien de spécial : on avance et on balaye la tête
                self._sweep_head()
                time.sleep(0.05)

        except KeyboardInterrupt:
            pass
        finally:
            self.robot.stop()
            self.robot.hazard_off()
            self.servos.set_angle(1, 90)
            self.servos.set_angle(0, self.ANGLE_CENTER_ROUE)


if __name__ == "__main__":
    StayInZone().run()