import sys
import time
import threading
from unittest.mock import MagicMock, patch, PropertyMock

for mod in ['gpiozero', 'spidev', 'numpy', 'board', 'busio',
            'adafruit_motor', 'adafruit_motor.servo', 'adafruit_motor.motor',
            'adafruit_pca9685', 'smbus']:
    sys.modules[mod] = MagicMock()

import tache5 as t5
import tache6 as t6
import tache9 as t9


def test_distance_sensor_converts_to_mm():
    sensor = t5.Distance()
    sensor.sensor.distance = 0.5
    assert sensor.checkdist() == 500.0


def test_distance_sensor_zero():
    sensor = t5.Distance()
    sensor.sensor.distance = 0.0
    assert sensor.checkdist() == 0.0


def test_distance_cleanup_calls_close():
    sensor = t5.Distance()
    sensor.cleanup()
    sensor.sensor.close.assert_called_once()


def test_line_follower_pin_mapping():
    lf = t6.LineFollower()
    assert lf.line_pin_left == 22
    assert lf.line_pin_middle == 27
    assert lf.line_pin_right == 17


def test_line_follower_reads_all_sensors():
    lf = t6.LineFollower()
    lf.left.value = 1
    lf.middle.value = 0
    lf.right.value = 1
    lf.run()


def test_robot_controller_demarrer_starts_motor():
    robot = t9.RobotController()
    robot.mc.drive_ramp = MagicMock()
    robot.desactiver_feux = MagicMock()
    robot.demarrer()
    assert robot.en_marche == True
    robot.mc.drive_ramp.assert_called_once_with(t9.RobotController.VITESSE_MARCHE, ramp_time=1.0)


def test_robot_controller_arreter_stops_motor():
    robot = t9.RobotController()
    robot.mc.drive_ramp = MagicMock()
    robot.en_marche = True
    robot.arreter()
    assert robot.en_marche == False
    robot.mc.drive_ramp.assert_called_once()


def test_robot_demarrer_idempotent():
    robot = t9.RobotController()
    robot.mc.drive_ramp = MagicMock()
    robot.desactiver_feux = MagicMock()
    robot.demarrer()
    robot.demarrer()
    robot.mc.drive_ramp.assert_called_once()


def test_robot_activer_feux_starts_thread():
    robot = t9.RobotController()
    with patch('threading.Thread') as mock_thread:
        mock_thread.return_value = MagicMock()
        robot.activer_feux()
        assert robot.feux_actifs == True
        mock_thread.assert_called_once()


def test_robot_activer_feux_idempotent():
    robot = t9.RobotController()
    with patch('threading.Thread') as mock_thread:
        mock_thread.return_value = MagicMock()
        robot.activer_feux()
        robot.activer_feux()
        mock_thread.assert_called_once()


def test_robot_desactiver_feux_sets_event():
    robot = t9.RobotController()
    robot.feux_actifs = True
    robot.desactiver_feux()
    assert robot.feux_actifs == False
    assert robot.stop_feux.is_set()


def test_robot_desactiver_feux_turns_off_leds():
    robot = t9.RobotController()
    robot.leds_gpio.set_all_switch_off = MagicMock()
    robot.leds_ws.turn_off_all = MagicMock()
    robot.feux_actifs = True
    robot.desactiver_feux()
    robot.leds_gpio.set_all_switch_off.assert_called_once()
    robot.leds_ws.turn_off_all.assert_called_once()


def test_obstacle_detection_triggers_stop_and_feux():
    robot = t9.RobotController()
    robot.mc.drive_ramp = MagicMock()
    robot.desactiver_feux = MagicMock()
    robot.arreter = MagicMock()
    robot.activer_feux = MagicMock()
    robot.en_marche = True

    robot.capteur.checkdist = MagicMock(return_value=50.0)

    robot.arreter()
    robot.activer_feux()

    robot.arreter.assert_called_once()
    robot.activer_feux.assert_called_once()


def test_vitesse_marche_constant():
    assert t9.RobotController.VITESSE_MARCHE == 0.2


def test_dist_obstacle_constant():
    assert t9.RobotController.DIST_OBSTACLE_MM == 200.0


def test_periode_capteur_constant():
    assert t9.RobotController.PERIODE_CAPTEUR == 0.05


if __name__ == "__main__":
    tests = [
        test_distance_sensor_converts_to_mm,
        test_distance_sensor_zero,
        test_distance_cleanup_calls_close,
        test_line_follower_pin_mapping,
        test_line_follower_reads_all_sensors,
        test_robot_controller_demarrer_starts_motor,
        test_robot_controller_arreter_stops_motor,
        test_robot_demarrer_idempotent,
        test_robot_activer_feux_starts_thread,
        test_robot_activer_feux_idempotent,
        test_robot_desactiver_feux_sets_event,
        test_robot_desactiver_feux_turns_off_leds,
        test_obstacle_detection_triggers_stop_and_feux,
        test_vitesse_marche_constant,
        test_dist_obstacle_constant,
        test_periode_capteur_constant,
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
