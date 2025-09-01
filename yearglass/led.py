from machine import Pin, Timer  # type: ignore


class Led:
    def __init__(self, pin_name: str = "LED") -> None:
        self.pin: Pin = Pin(pin_name, Pin.OUT)
        self._timer: Timer | None = None
        self._blinking: bool = False
        self._interval_ms: int = 1000

    def on(self) -> None:
        self.pin.value(1)

    def off(self) -> None:
        self.pin.value(0)

    def blink_on(self, interval: float = 1.0) -> None:
        """
        Start non-blocking blinking with the given interval in seconds (default 1.0s).
        """
        if self._blinking:
            return
        self._interval_ms = int(interval * 1000)
        self._blinking = True
        timer = Timer()
        timer.init(period=self._interval_ms, mode=Timer.PERIODIC, callback=self._toggle)
        self._timer = timer

    def blink_off(self) -> None:
        """
        Stop blinking and turn the LED off.
        """
        if self._timer is not None:
            self._timer.deinit()
            self._timer = None
        self._blinking = False
        self.off()

    def _toggle(self, timer: Timer) -> None:
        self.pin.value(0 if self.pin.value() else 1)
