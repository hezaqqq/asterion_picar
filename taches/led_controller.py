from gpiozero import LED

class RobotLEDController:

    LED_CONFIG = {
        1: {"gpio": 9,  "active_high": True},
        2: {"gpio": 25, "active_high": True},
        3: {"gpio": 11, "active_high": True},
        4: {"gpio": 0,  "active_high": False},
        5: {"gpio": 19, "active_high": False},
        6: {"gpio": 13, "active_high": False},
        7: {"gpio": 1,  "active_high": False},
        8: {"gpio": 5,  "active_high": False},
        9: {"gpio": 6,  "active_high": False},
    }

    def __init__(self):
        self.leds: dict[int, LED] = {}

    def setup(self):
        for led_id, cfg in self.LED_CONFIG.items():
            self.leds[led_id] = LED(cfg["gpio"], active_high=cfg["active_high"], initial_value=False)

    def led_on(self, led_id: int):
        if led_id not in self.leds:
            raise ValueError(f"LED {led_id} inexistante.")
        self.leds[led_id].on()

    def led_off(self, led_id: int):
        if led_id not in self.leds:
            raise ValueError(f"LED {led_id} inexistante.")
        self.leds[led_id].off()

    def all_off(self):
        for led_id in self.leds:
            self.leds[led_id].off()

if __name__ == "__main__":
    controller = RobotLEDController()
    controller.setup()
    while True:
        controller.led_on(6)
        controller.led_on(7)
        controller.led_on(9)
        controller.led_on(8)