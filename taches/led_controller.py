from gpiozero import LED
from gpiozero.exc import GPIOPinInUse

class RobotLEDController:

    LED_CONFIG = {
        5: {"gpio": 19, "active_high": False},
        6: {"gpio": 13, "active_high": False},
        7: {"gpio": 1,  "active_high": False},
        8: {"gpio": 5,  "active_high": False},
    }

    def __init__(self):
        self.leds: dict[int, LED] = {}

    def setup(self):
        for led_id, cfg in self.LED_CONFIG.items():
            try:
                self.leds[led_id] = LED(cfg["gpio"], active_high=cfg["active_high"], initial_value=False)
            except GPIOPinInUse:
                pass

    def led_on(self, led_id: int):
        if led_id in self.leds:
            self.leds[led_id].on()

    def led_off(self, led_id: int):
        if led_id in self.leds:
            self.leds[led_id].off()

    def all_off(self):
        for led_id in self.leds:
            self.leds[led_id].off()