import robot_controller as robot_controller
import ultrasonic_sensor as ultrasonic_sensor
import servo_controller as servo

import time
import threading

ANGLE_CENTER_ROUE    = 100
ANGLE_MIN_ROUE       = 60
ANGLE_MAX_ROUE       = 140

ANGLE_CENTER_TETE_GD = 108
ANGLE_MIN_TETE_GD    = 48
ANGLE_MAX_TETE_GD    = 168

if __name__ == "__main__":
    robot = None
    try:
        sensor = ultrasonic_sensor.UltrasonicSensor()
        robot = robot_controller.RobotController(sensor=sensor)
        servos = servo.ServoController()

        servos.set_angle(1, ANGLE_CENTER_TETE_GD)
        servos.set_angle(2, 75)
        servos.set_angle(0, ANGLE_CENTER_ROUE)

        gauche       = True
        angle_tete_gd = ANGLE_CENTER_TETE_GD
        around = False

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
            
            if sensor.get_distance_mm() < 150 and around == False:
                angle_before_around = angle_tete_gd
                if 48 <= angle_tete_gd <=108:
                    servos.set_angle(0, ANGLE_CENTER_ROUE-20)
                    time.sleep(3)
                    servos.set_angle(0, ANGLE_CENTER_ROUE+20)
                    time.sleep(3)
                    servos.set_angle(0, ANGLE_CENTER_ROUE) 
                
                else:
                    servos.set_angle(0, ANGLE_CENTER_ROUE+20)
                    time.sleep(3)
                    servos.set_angle(0, ANGLE_CENTER_ROUE-20)
                    time.sleep(3)
                    servos.set_angle(0, ANGLE_CENTER_ROUE) 
                    

            servos.set_angle(1, angle_tete_gd)
            time.sleep(0.05)

    except KeyboardInterrupt:
        if robot:
            robot.stop()
            robot.hazard_off()
        servos.set_angle(1, ANGLE_CENTER_TETE_GD)