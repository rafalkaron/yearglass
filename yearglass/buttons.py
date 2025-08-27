import utime  # type: ignore
from machine import Pin  # type: ignore


class Buttons:
    def __init__(
        self, key1_pin: int, key2_pin: int, key3_pin: int, on_key1, on_key2, on_key3
    ) -> None:
        self.key1 = Pin(key1_pin, Pin.IN, Pin.PULL_UP)
        self.key2 = Pin(key2_pin, Pin.IN, Pin.PULL_UP)
        self.key3 = Pin(key3_pin, Pin.IN, Pin.PULL_UP)
        self.on_key1 = on_key1
        self.on_key2 = on_key2
        self.on_key3 = on_key3

        # Set up interrupts for falling edge (button press)
        self.key1.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_key1)
        self.key2.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_key2)
        self.key3.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_key3)

    def enable_interrupts(self) -> None:
        self.key1.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_key1)
        self.key2.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_key2)
        self.key3.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_key3)

    def disable_interrupts(self) -> None:
        self.key1.irq(handler=None)
        self.key2.irq(handler=None)
        self.key3.irq(handler=None)

    def _handle_key1(self, pin):
        utime.sleep_ms(20)  # debounce
        if pin.value() == 0:
            print("[handle_buttons] KEY1 pressed (IRQ)")
            self.on_key1()
            self.wait_release(pin)

    def _handle_key2(self, pin):
        utime.sleep_ms(20)
        if pin.value() == 0:
            print("[handle_buttons] KEY2 pressed (IRQ)")
            self.on_key2()
            self.wait_release(pin)

    def _handle_key3(self, pin):
        utime.sleep_ms(20)
        if pin.value() == 0:
            print("[handle_buttons] KEY3 pressed (IRQ)")
            self.on_key3()
            self.wait_release(pin)

    def wait_release(self, pin: Pin) -> None:
        while pin.value() == 0:
            utime.sleep_ms(10)
