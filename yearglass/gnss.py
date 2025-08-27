from machine import Pin

class Gnss:
    def __init__(self, sleep_pin = None):
        self.sleep = Pin(sleep_pin, Pin.OUT) if sleep_pin is not None else None

    def sleep(self) -> None:
        """Put GNSS module to sleep (if sleep pin is available)."""
        if self.sleep is not None:
            self.sleep.value(1)

    def wake(self) -> None:
        """Wake GNSS module from sleep (if sleep pin is available)."""
        if self.sleep is not None:
            self.sleep.value(0)
