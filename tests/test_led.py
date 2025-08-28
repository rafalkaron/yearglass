import utime as time  # type: ignore

from yearglass.led import Led


class TestLed:
    def __init__(self):
        self.led = Led()

    def test_on(self):
        self.led.off()
        self.led.on()
        assert self.led.pin.value() == 1
        time.sleep(3)

    def test_off(self):
        self.led.on()
        self.led.off()
        assert self.led.pin.value() == 0
        time.sleep(3)

    def test_blink_on_sets_state(self):
        self.led.blink_on(0.2)
        assert self.led._blinking is True
        assert self.led._timer is not None
        assert self.led._interval_ms == 200
        time.sleep(3)

    def test_blink_off_resets_state(self):
        self.led.blink_on(0.1)
        self.led.on()
        self.led.blink_off()
        assert self.led._blinking is False
        assert self.led._timer is None
        assert self.led.pin.value() == 0
        time.sleep(3)

    def test_toggle(self):
        self.led.off()
        self.led._toggle(self.led._timer)
        assert self.led.pin.value() == 1
        self.led._toggle(self.led._timer)
        assert self.led.pin.value() == 0
        time.sleep(3)

    def run_all(self):
        self.test_on()
        self.test_off()
        self.test_blink_on_sets_state()
        self.test_blink_off_resets_state()
        self.test_toggle()


if __name__ == "__main__":
    test = TestLed()
    test.run_all()
