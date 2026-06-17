from gpiozero import DistanceSensor

class UltrasonicSensor:
    TRIGGER_PIN = 23
    ECHO_PIN    = 24
    MAX_DIST_M  = 2.0

    def __init__(self):
        self.sensor = DistanceSensor(
            echo=self.ECHO_PIN,
            trigger=self.TRIGGER_PIN,
            max_distance=self.MAX_DIST_M,
        )

    def get_distance_mm(self) -> float:
        return self.sensor.distance * 1000.0

    def release(self):
        self.sensor.close()