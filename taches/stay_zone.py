import line_reading as line_reading
import robot_controller as robot_module
import servo_controller as servo_module
import ultrasonic_sensor as ultrasonic_module
import time

class StayInZone:

    ANGLE_CENTER_ROUE = 100
    ANGLE_MIN_ROUE    = 60
    ANGLE_MAX_ROUE    = 140

    ANGLE_CENTER_TETE_GD = 108
    ANGLE_MIN_TETE_GD    = 48
    ANGLE_MAX_TETE_GD    = 168

    SPEED_STRAIGHT = 0.25
    SPEED_CURVE    = 0.20

    REVERSE_TIME   = 2
    RAMP_TIME      = 0.2

    OBSTACLE_DIST_MM = 150

    def __init__(self):
        self.sensor    = ultrasonic_module.UltrasonicSensor()
        self.robot     = robot_module.RobotController(sensor=self.sensor)
        self.line      = line_reading.LineReading()
        self.servos    = servo_module.ServoController()
        self._running  = False
        self._last_side = self.ANGLE_MAX_ROUE  # dernier côté de ligne détecté

        # État du balayage de tête (remplace les variables locales de detection.py)
        self._gauche        = True
        self._angle_tete_gd = self.ANGLE_CENTER_TETE_GD

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
            self._angle_tete_gd += 1
            if self._angle_tete_gd >= self.ANGLE_MAX_TETE_GD:
                self._gauche = False
        else:
            self._angle_tete_gd -= 1
            if self._angle_tete_gd <= self.ANGLE_MIN_TETE_GD:
                self._gauche = True
        self.servos.set_angle(1, self._angle_tete_gd)

    def _check_obstacle(self) -> bool:
        if self.sensor.get_distance_mm() >= self.OBSTACLE_DIST_MM:
            return False

        self.robot._watch_enabled = False   # ← suspend la surveillance auto
        self.robot.stop()

        if self.ANGLE_MIN_TETE_GD <= self._angle_tete_gd <= self.ANGLE_CENTER_TETE_GD:
            self.servos.set_angle(0, self.ANGLE_CENTER_ROUE + 30)
            time.sleep(3)
            self.servos.set_angle(0, self.ANGLE_CENTER_ROUE - 30)
            time.sleep(3)
        else:
            self.servos.set_angle(0, self.ANGLE_CENTER_ROUE - 30)
            time.sleep(3)
            self.servos.set_angle(0, self.ANGLE_CENTER_ROUE + 30)
            time.sleep(3)

        self.servos.set_angle(0, self.ANGLE_CENTER_ROUE)
        self.robot.hazard_off()
        self.robot.SPEED = self.SPEED_STRAIGHT
        self.robot._watch_enabled = True    # ← réactive la surveillance
        self.robot.start()
        return True

    # ── Boucle principale ────────────────────────────────────────────
    def run(self):
        self.servos.set_angle(0, self.ANGLE_CENTER_ROUE)
        self.servos.set_angle(1, self.ANGLE_CENTER_TETE_GD)
        self.servos.set_angle(2, 75)
        self.robot.SPEED = self.SPEED_STRAIGHT
        self.robot.start()

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
            self.servos.set_angle(1, self.ANGLE_CENTER_TETE_GD)
            self.servos.set_angle(0, self.ANGLE_CENTER_ROUE)


if __name__ == "__main__":
    StayInZone().run()