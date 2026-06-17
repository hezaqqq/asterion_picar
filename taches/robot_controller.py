import time
import threading

import led_controller as led
import WS2812_led_controller as ws_led
import motor_controller as motor
import ultrasonic_sensor as ultrasonic_sensor


class RobotController:
    SPEED           = 0.25 
    OBSTACLE_MM     = 200.0   # distance
    SENSOR_PERIOD   = 0.05    # période du capteur (s)

    def __init__(self, sensor=None):
        self.gpio_leds  = led.RobotLEDController()
        self.gpio_leds.setup()

        self.ws_leds    = ws_led.LEDController(led_count=14)
        self.ws_leds.all_off()

        self.motors     = motor.MotorController()
        self.sensor     = sensor if sensor is not None else ultrasonic_sensor.UltrasonicSensor()

        self.moving      = False
        self._hazard_on  = False
        self._stop_hazard = threading.Event()

        threading.Thread(target=self._watch_distance, daemon=True).start()


    def start(self):
        if self.moving:
            return
        self.moving = True
        self.motors.drive(self.SPEED, ramp_time=1.0)

    def stop(self, ramp_time: float = 0.05):
        self.moving = False
        self.motors.drive(0.0, ramp_time=ramp_time)


    def clignotants_on(self):
        """Active les feux de détresse clignotants (thread daemon)."""
        if self._hazard_on:
            return
        self._hazard_on = True
        self._stop_hazard.clear()
        threading.Thread(target=self._blink_hazard, daemon=True).start()

    def clignotants_off(self):
        if not self._hazard_on:
            return
        self._stop_hazard.set()
        self._hazard_on = False
        self.gpio_leds.all_off()
        self.ws_leds.all_off()

    def _watch_distance(self):
        while True:
            if self.moving:
                dist = self.sensor.get_distance_mm()
                if dist < self.OBSTACLE_MM:
                    self.stop()
                    self.hazard_on()
            time.sleep(self.SENSOR_PERIOD)


    def release(self):
        self.stop()
        self.hazard_off()
        self.motors.release()
        self.sensor.release()