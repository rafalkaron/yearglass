from machine import Pin  # type: ignore


class Led:
    def __init__(self, pin_name: str = "LED") -> None:
        self.pin: Pin = Pin(pin_name, Pin.OUT)

    def on(self) -> None:
        self.pin.value(1)

    def off(self) -> None:
        self.pin.value(0)
