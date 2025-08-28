from machine import Pin, UART


class Gnss:
    """
    GNSS module interface for Raspberry Pi Pico W.

    Initializes and manages UART communication with a GNSS module and controls a sleep pin.
    
    Args:
        uart_id (int): UART port number (default 0).
        tx (int): TX pin number (default 0, typically GP0).
        rx (int): RX pin number (default 1, typically GP1).
        baudrate (int): UART baudrate (default 9600).
        sleep_pin (int): Pin number for GNSS sleep control.

    Attributes:
        uart: Initialized UART object for GNSS communication.
        sleep: Pin object for sleep control, or None if not used.
    """
    def __init__(
        self,
        uart_id: int = 0,
        tx: int = 0,
        rx: int = 1,
        baudrate: int = 9600,
        wup: int = 6
    ):
        self.uart = UART(uart_id, baudrate=baudrate, tx=tx, rx=rx)
        self.wup = Pin(wup, Pin.OUT)

    def sleep(self) -> None:
        """Put GNSS module to sleep (if sleep pin is available)."""
        self.wup.value(1)

    def wake(self) -> None:
        """Wake GNSS module from sleep (if sleep pin is available)."""
        self.wup.value(0)
