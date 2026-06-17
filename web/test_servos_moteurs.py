import sys
import time
from unittest.mock import MagicMock, patch, PropertyMock

for mod in ['board', 'busio', 'adafruit_motor', 'adafruit_motor.servo',
            'adafruit_motor.motor', 'adafruit_pca9685', 'gpiozero']:
    sys.modules[mod] = MagicMock()

import tache3 as t3
import tache4 as t4


def test_servo_angle_clamped_above_max():
    ctrl = t3.ServoController()
    ctrl.pca = MagicMock()
    servo_mock = MagicMock()
    with patch('tache3.servo.Servo', return_value=servo_mock):
        ctrl.set_angle(0, 999)
        assert servo_mock.angle == 140


def test_servo_angle_clamped_below_min():
    ctrl = t3.ServoController()
    ctrl.pca = MagicMock()
    servo_mock = MagicMock()
    with patch('tache3.servo.Servo', return_value=servo_mock):
        ctrl.set_angle(0, -50)
        assert servo_mock.angle == 60


def test_servo_angle_exact_boundary():
    ctrl = t3.ServoController()
    ctrl.pca = MagicMock()
    servo_mock = MagicMock()
    with patch('tache3.servo.Servo', return_value=servo_mock):
        ctrl.set_angle(7, 0)
        assert servo_mock.angle == 0
        ctrl.set_angle(7, 185)
        assert servo_mock.angle == 185


def test_servo_unknown_channel_defaults_0_180():
    ctrl = t3.ServoController()
    ctrl.pca = MagicMock()
    servo_mock = MagicMock()
    with patch('tache3.servo.Servo', return_value=servo_mock):
        ctrl.set_angle(5, 90)
        assert servo_mock.angle == 90
        ctrl.set_angle(5, 200)
        assert servo_mock.angle == 180


def test_center_all_calls_set_angle():
    ctrl = t3.ServoController()
    ctrl.set_angle = MagicMock()
    with patch('tache3.time.sleep'):
        ctrl.center_all()
    expected_channels = list(ctrl.SAFE_ANGLES.keys())
    called_channels = [c.args[0] for c in ctrl.set_angle.call_args_list]
    assert sorted(called_channels) == sorted(expected_channels)
    for c in ctrl.set_angle.call_args_list:
        assert c.args[1] == 100


def test_servo_tester_sequence():
    ctrl = t3.ServoController()
    ctrl.set_angle = MagicMock()
    tester = t3.ServoTester(ctrl)
    with patch('tache3.time.sleep'):
        tester.run()
    angles_called = [c.args[1] for c in ctrl.set_angle.call_args_list]
    expected = [s[0] for s in t3.ServoTester.SEQUENCE]
    assert angles_called == expected


def test_motor_controller_drive_ramp_clamps():
    mc = t4.MotorController()
    mc._set_all_motors = MagicMock()
    mc.drive_ramp(5.0, ramp_time=0.001)
    calls = [c.args[0] for c in mc._set_all_motors.call_args_list]
    assert max(calls) <= 1.0


def test_motor_controller_drive_ramp_negative_clamps():
    mc = t4.MotorController()
    mc._set_all_motors = MagicMock()
    mc.drive_ramp(-9.0, ramp_time=0.001)
    calls = [c.args[0] for c in mc._set_all_motors.call_args_list]
    assert min(calls) >= -1.0


def test_motor_drive_ramp_updates_current_throttle():
    mc = t4.MotorController()
    mc._set_all_motors = MagicMock()
    mc.drive_ramp(0.5, ramp_time=0.001)
    assert mc.current_throttle == 0.5
    mc.drive_ramp(-0.3, ramp_time=0.001)
    assert mc.current_throttle == -0.3


def test_motor_map_function():
    mc = t4.MotorController()
    assert mc._map(5, 0, 10, 0, 100) == 50.0
    assert mc._map(0, 0, 10, 0, 100) == 0.0
    assert mc._map(10, 0, 10, 0, 100) == 100.0


def test_servo_pulse_config():
    assert t3.ServoController.MIN_PULSE == 500
    assert t3.ServoController.MAX_PULSE == 2400


def test_motor_servo_channel_values():
    assert t4.MotorController.SERVO_LEFT   == 3277
    assert t4.MotorController.SERVO_CENTER == 4915
    assert t4.MotorController.SERVO_RIGHT  == 6554


def test_destroy_stops_motors():
    mc = t4.MotorController()
    mc._set_all_motors = MagicMock()
    mc.pwm_motor = MagicMock()
    mc.destroy()
    mc._set_all_motors.assert_called_with(0)
    mc.pwm_motor.deinit.assert_called_once()


if __name__ == "__main__":
    tests = [
        test_servo_angle_clamped_above_max,
        test_servo_angle_clamped_below_min,
        test_servo_angle_exact_boundary,
        test_servo_unknown_channel_defaults_0_180,
        test_center_all_calls_set_angle,
        test_servo_tester_sequence,
        test_motor_controller_drive_ramp_clamps,
        test_motor_controller_drive_ramp_negative_clamps,
        test_motor_drive_ramp_updates_current_throttle,
        test_motor_map_function,
        test_servo_pulse_config,
        test_motor_servo_channel_values,
        test_destroy_stops_motors,
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
