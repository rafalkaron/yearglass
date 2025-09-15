import utime  # type: ignore
from machine import Pin  # type: ignore

from .usbprint import usbprint


class Buttons:
    def __init__(
        self,
        key1_pin: int,
        key2_pin: int,
        key3_pin: int,
        on_key1,
        on_key2,
        on_key3,
        on_key1_long=None,
        on_key2_long=None,
        on_key3_long=None,
        long_press_ms: int = 5000,
    ) -> None:
        self.key1 = Pin(key1_pin, Pin.IN, Pin.PULL_UP)
        self.key2 = Pin(key2_pin, Pin.IN, Pin.PULL_UP)
        self.key3 = Pin(key3_pin, Pin.IN, Pin.PULL_UP)
        self.on_key1 = on_key1
        self.on_key2 = on_key2
        self.on_key3 = on_key3
        self.on_key1_long = on_key1_long
        self.on_key2_long = on_key2_long
        self.on_key3_long = on_key3_long
        self.long_press_ms = long_press_ms

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
            usbprint("[handle_buttons] KEY1 pressed (IRQ)")
            self._handle_press(pin, self.on_key1, self.on_key1_long, "KEY1")

    def _handle_key2(self, pin):
        utime.sleep_ms(20)
        if pin.value() == 0:
            usbprint("[handle_buttons] KEY2 pressed (IRQ)")
            self._handle_press(pin, self.on_key2, self.on_key2_long, "KEY2")

    def _handle_key3(self, pin):
        utime.sleep_ms(20)
        if pin.value() == 0:
            usbprint("[handle_buttons] KEY3 pressed (IRQ)")
            self._handle_press(pin, self.on_key3, self.on_key3_long, "KEY3")

    def _handle_press(self, pin: Pin, short_cb, long_cb, key_name: str) -> None:
        press_time = utime.ticks_ms()
        while pin.value() == 0:
            utime.sleep_ms(10)
        release_time = utime.ticks_ms()
        duration = utime.ticks_diff(release_time, press_time)
        if duration >= self.long_press_ms and long_cb:
            usbprint(f"[handle_buttons] {key_name} long-press detected ({duration} ms)")
            long_cb()
        else:
            usbprint(
                f"[handle_buttons] {key_name} short-press detected ({duration} ms)"
            )
            short_cb()
