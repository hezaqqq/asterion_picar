import robot_controller as robot_controller
import ultrasonic_sensor as ultrasonic_sensor
import servo_controller as servo

import time
import threading

ANGLE_CENTER_ROUE    = 100
ANGLE_MIN_ROUE       = 60
ANGLE_MAX_ROUE       = 140
ANGLE_CENTER_TETE_GD = 108
ANGLE_MIN_TETE_GD    = 78
ANGLE_MAX_TETE_GD    = 138

if __name__ == "__main__":
    robot = None
    try:
        sensor     = ultrasonic_sensor.UltrasonicSensor()
        robot      = robot_controller.RobotController()
        controller = servo.ServoController()

        controller.set_angle(1, ANGLE_CENTER_TETE_GD)
        controller.set_angle(2, 75)
        controller.set_angle(0, ANGLE_CENTER_ROUE)

        gauche       = True
        angle_tete_gd = ANGLE_CENTER_TETE_GD

        threading.Thread(target=robot._surveiller_distance, daemon=True).start()
        robot.demarrer()

        while True:
            # Balayage tête
            if gauche:
                angle_tete_gd += 1
                if angle_tete_gd >= ANGLE_MAX_TETE_GD:
                    gauche = False
            else:
                angle_tete_gd -= 1
                if angle_tete_gd <= ANGLE_MIN_TETE_GD:
                    gauche = True
            controller.set_angle(1, angle_tete_gd)
            time.sleep(0.05)

    except KeyboardInterrupt:
        if robot:
            robot.mc._set_all_motors(0)
            robot.desactiver_feux()
        controller.set_angle(1, ANGLE_CENTER_TETE_GD)
        robot.mc.pwm_motor.deinit()