from gpiozero import InputDevice

class LineReading:
    PIN_LEFT   = 22
    PIN_MIDDLE = 27
    PIN_RIGHT  = 17

    def __init__(self):
        self._left   = InputDevice(pin=self.PIN_RIGHT)
        self._middle = InputDevice(pin=self.PIN_MIDDLE)
        self._right  = InputDevice(pin=self.PIN_LEFT)

    def line_read(self) -> tuple[int, int, int]:
        return (
            self._left.value,
            self._middle.value,
            self._right.value,
        )