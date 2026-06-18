import robot_controller as robot_controller
import ultrasonic_sensor as ultrasonic_sensor
import servo_controller as servo
import time

ANGLE_CENTER_ROUE    = 100
ANGLE_MIN_ROUE       = 60
ANGLE_MAX_ROUE       = 140

ANGLE_CENTER_TETE_GD = 108
ANGLE_MIN_TETE_GD    = 48
ANGLE_MAX_TETE_GD    = 168

OBSTACLE_DIST_CM     = 30    # distance seuil pour évitement
STEER_DELTA          = 20    # degrés de braquage roues
STEER_HOLD_TICKS     = 10    # combien de ticks on maintient le braquage (~0.5s)

if __name__ == "__main__":
    robot = None
    try:
        sensor = ultrasonic_sensor.UltrasonicSensor()
        robot  = robot_controller.RobotController(sensor=sensor)
        servos = servo.ServoController()

        servos.set_angle(1, ANGLE_CENTER_TETE_GD)
        servos.set_angle(2, 75)
        servos.set_angle(0, ANGLE_CENTER_ROUE)

        gauche        = True
        angle_tete_gd = ANGLE_CENTER_TETE_GD
        steer_angle   = ANGLE_CENTER_ROUE
        steer_hold    = 0 

        while True:
            if gauche:
                angle_tete_gd += 1
                if angle_tete_gd >= ANGLE_MAX_TETE_GD:
                    gauche = False
            else:
                angle_tete_gd -= 1
                if angle_tete_gd <= ANGLE_MIN_TETE_GD:
                    gauche = True
            servos.set_angle(1, angle_tete_gd)

            dist = sensor.get_distance_mm()

            if dist is not None and dist < OBSTACLE_DIST_CM:
                # Obstacle donc on va vers le côté opposé à la tête
                if angle_tete_gd < ANGLE_CENTER_TETE_GD:
                    steer_angle = min(ANGLE_MAX_ROUE, ANGLE_CENTER_ROUE + STEER_DELTA)
                else:
                    steer_angle = max(ANGLE_MIN_ROUE, ANGLE_CENTER_ROUE - STEER_DELTA)
                steer_hold = STEER_HOLD_TICKS
            else:
                # Pas d'obstacle
                if steer_hold > 0:
                    steer_hold -= 1
                else:
                    steer_angle = ANGLE_CENTER_ROUE

            servos.set_angle(0, steer_angle)
            time.sleep(0.05)

    except KeyboardInterrupt:
        if robot:
            robot.stop()
            robot.hazard_off()
        servos.set_angle(1, ANGLE_CENTER_TETE_GD)
        servos.set_angle(0, ANGLE_CENTER_ROUE)