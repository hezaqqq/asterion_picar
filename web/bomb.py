#!/usr/bin/env python3
import time
import numpy
import spidev
from gpiozero import PWMOutputDevice
from gpiozero import LED

try:
    # Bypasses TonalBuzzer constraints entirely. Uses raw hardware PWM.
    tb = PWMOutputDevice(18, frequency=1000, initial_value=0.0)
except Exception as e:
    print(f"Buzzer initialization error: {e}")
    tb = None

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
gpio_leds = {}

class LEDController:
    def __init__(self, led_count=14):
        self.led_count = led_count
        self.led_color = [0] * (self.led_count * 3)
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.mode = 0

    def set_all_red(self, brightness=255):
        for i in range(self.led_count):
            self.led_color[i * 3 + 1] = brightness
            self.led_color[i * 3 + 0] = 0
            self.led_color[i * 3 + 2] = 0
        self.show()

    def show(self):
        d = numpy.array(self.led_color).ravel()
        tx = numpy.zeros(len(d) * 8, dtype=numpy.uint8)
        for ibit in range(8):
            tx[7 - ibit :: 8] = ((d >> ibit) & 1) * 0x78 + 0x80
        self.spi.xfer(tx.tolist(), int(8 / 1.25e-6))

    def turn_off_all(self):
        self.led_color = [0] * (self.led_count * 3)
        self.show()

def setup_hardware():
    global gpio_leds
    for led_id, config in LED_CONFIG.items():
        gpio_leds[led_id] = LED(config["gpio"], active_high=config["active_high"], initial_value=False)

def set_lights(state):
    if state:
        spi_controller.set_all_red(255)
        for led in gpio_leds.values():
            led.on()
    else:
        spi_controller.turn_off_all()
        for led in gpio_leds.values():
            led.off()

def play_sound(frequency):
    if tb:
        tb.frequency = int(frequency)
        tb.value = 0.5  # 50% duty cycle creates the sound wave

def stop_sound():
    if tb:
        tb.value = 0.0  # Turn off the wave

def play_bomb_sequence():
    total_steps = 25
    start_freq = 1000
    end_freq = 3800
    start_delay = 0.6
    end_delay = 0.04

    try:
        # Initial test beep
        play_sound(1500)
        time.sleep(0.3)
        stop_sound()
        time.sleep(0.2)

        for step in range(total_steps):
            progress = step / float(total_steps - 1)
            current_freq = start_freq + (end_freq - start_freq) * progress
            current_delay = start_delay - (start_delay - end_delay) * progress
            pulse_duration = current_delay * 0.4
            
            set_lights(True)
            play_sound(current_freq)
            time.sleep(pulse_duration)
            
            stop_sound()
            set_lights(False)
            time.sleep(current_delay - pulse_duration)
            
        # Explosion pitch drop
        set_lights(True)
        for freq in range(2000, 150, -60):
            play_sound(freq)
            time.sleep(0.01)
            
        stop_sound()
        time.sleep(1)
        
    except KeyboardInterrupt:
        pass
    finally:
        stop_sound()
        set_lights(False)

if __name__ == "__main__":
    spi_controller = LEDController(led_count=14)
    setup_hardware()
    set_lights(False)
    play_bomb_sequence()

