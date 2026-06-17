import numpy
import spidev

class LEDController:
    def __init__(self, led_count: int = 14):
        self.led_count = led_count
        self.led_color = [0] * (led_count * 3)
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.mode = 0

    def set_led(self, index: int, r: int, g: int, b: int, brightness: int = 255):
        if not (0 <= index < self.led_count):
            raise ValueError(f"Index LED invalide : {index} (0–{self.led_count - 1})")
        self.led_color[index * 3 + 1] = round(r * brightness / 255)
        self.led_color[index * 3 + 0] = round(g * brightness / 255)
        self.led_color[index * 3 + 2] = round(b * brightness / 255)
        self._show()

    def all_off(self):
        self.led_color = [0] * (self.led_count * 3)
        self._show()

    def _show(self):
        d = numpy.array(self.led_color).ravel()
        tx = numpy.zeros(len(d) * 8, dtype=numpy.uint8)
        for ibit in range(8):
            tx[7 - ibit :: 8] = ((d >> ibit) & 1) * 0x78 + 0x80
        self.spi.xfer(tx.tolist(), int(8 / 1.25e-6))