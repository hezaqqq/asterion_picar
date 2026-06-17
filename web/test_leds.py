import time
from unittest.mock import MagicMock, patch, call
import sys

sys.modules['gpiozero'] = MagicMock()
sys.modules['spidev'] = MagicMock()
sys.modules['numpy'] = MagicMock()

import importlib
import types

gpiozero_mock = sys.modules['gpiozero']
LED_mock = MagicMock()
gpiozero_mock.LED = LED_mock

import tache1 as t1
import tache2 as t2


def test_switchSetup_creates_all_leds():
    LED_mock.reset_mock()
    ctrl = t1.RobotLEDController()
    ctrl.switchSetup()
    assert len(ctrl.leds) == 9
    assert LED_mock.call_count == 9


def test_switch_on_calls_on():
    ctrl = t1.RobotLEDController()
    ctrl.switchSetup()
    ctrl.switch(1, 1)
    ctrl.leds[1].on.assert_called_once()


def test_switch_off_calls_off():
    ctrl = t1.RobotLEDController()
    ctrl.switchSetup()
    ctrl.switch(2, 0)
    ctrl.leds[2].off.assert_called_once()


def test_switch_invalid_led(capsys=None):
    ctrl = t1.RobotLEDController()
    ctrl.switchSetup()
    ctrl.switch(99, 1)


def test_set_all_switch_off():
    ctrl = t1.RobotLEDController()
    ctrl.switchSetup()
    ctrl.switch(1, 1)
    ctrl.switch(3, 1)
    ctrl.set_all_switch_off()
    for led in ctrl.leds.values():
        led.off.assert_called()


def test_led_config_gpio_pins():
    ctrl = t1.RobotLEDController()
    assert ctrl.LED_CONFIG[1]["gpio"] == 9
    assert ctrl.LED_CONFIG[4]["active_high"] == False
    assert ctrl.LED_CONFIG[7]["gpio"] == 1


def test_ws_led_init():
    ctrl = t2.LEDController(led_count=14)
    assert ctrl.led_count == 14
    assert len(ctrl.led_color) == 42


def test_ws_set_led_invalid_index():
    ctrl = t2.LEDController(led_count=14)
    ctrl.show = MagicMock()
    ctrl.set_led(99, 255, 0, 0)
    ctrl.show.assert_not_called()


def test_ws_set_led_brightness_scaling():
    ctrl = t2.LEDController(led_count=14)
    ctrl.show = MagicMock()

    import numpy as real_numpy
    sys.modules['numpy'] = real_numpy

    ctrl2 = t2.LEDController(led_count=14)
    ctrl2.show = MagicMock()
    ctrl2.set_led(0, 200, 100, 50, brightness=128)
    assert ctrl2.led_color[1] == round(200 * 128 / 255)
    assert ctrl2.led_color[0] == round(100 * 128 / 255)
    assert ctrl2.led_color[2] == round(50  * 128 / 255)


def test_ws_turn_off_all():
    import numpy as real_numpy
    sys.modules['numpy'] = real_numpy

    ctrl = t2.LEDController(led_count=14)
    ctrl.led_color = [255] * 42
    ctrl.show = MagicMock()
    ctrl.turn_off_all()
    assert all(v == 0 for v in ctrl.led_color)


def test_active_high_false_leds():
    ctrl = t1.RobotLEDController()
    active_low_ids = [4, 5, 6, 7, 8, 9]
    for led_id in active_low_ids:
        assert ctrl.LED_CONFIG[led_id]["active_high"] == False


if __name__ == "__main__":
    tests = [
        test_switchSetup_creates_all_leds,
        test_switch_on_calls_on,
        test_switch_off_calls_off,
        test_switch_invalid_led,
        test_set_all_switch_off,
        test_led_config_gpio_pins,
        test_ws_led_init,
        test_ws_set_led_invalid_index,
        test_ws_set_led_brightness_scaling,
        test_ws_turn_off_all,
        test_active_high_false_leds,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗  {t.__name__} → {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
