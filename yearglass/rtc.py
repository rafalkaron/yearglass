from machine import I2C, Pin


class Rtc:
    """
    RTC controller for PCF8563 I2C module on Raspberry Pi Pico W (MicroPython).
    Allows reading and setting date/time using I2C.
    If no I2C object is provided, initializes I2C(0) on GP4 (SDA) and GP5 (SCL).
    """

    def __init__(self, i2c: I2C | None = None, address: int = 0x51):
        """
        Initialize RTC with given I2C bus and device address.
        If i2c is None, initializes I2C(0) on GP4 (SDA) and GP5 (SCL).
        :param i2c: Initialized I2C object or None
        :param address: I2C address of PCF8563 (default 0x51)
        """
        if i2c is None:
            self.i2c = I2C(0, scl=Pin(5), sda=Pin(4))
        else:
            self.i2c = i2c
        self.address = address

    def _bcd2dec(self, bcd: int) -> int:
        """
        Convert BCD (Binary Coded Decimal) to integer.
        :param bcd: BCD value
        :return: Integer value
        """
        return (bcd // 16) * 10 + (bcd % 16)

    def _dec2bcd(self, dec: int) -> int:
        """
        Convert integer to BCD (Binary Coded Decimal).
        :param dec: Integer value
        :return: BCD value
        """
        return (dec // 10) * 16 + (dec % 10)

    def get_datetime(self) -> tuple:
        """
        Read current date and time from RTC.
        :return: Tuple (year, month, day, weekday, hour, minute, second)
        """
        data = self.i2c.readfrom_mem(self.address, 0x02, 7)
        second = self._bcd2dec(data[0] & 0x7F)
        minute = self._bcd2dec(data[1] & 0x7F)
        hour = self._bcd2dec(data[2] & 0x3F)
        day = self._bcd2dec(data[3] & 0x3F)
        weekday = self._bcd2dec(data[4] & 0x07)
        month = self._bcd2dec(data[5] & 0x1F)
        year = 2000 + self._bcd2dec(data[6])
        return (year, month, day, weekday, hour, minute, second)

    def set_datetime(
        self,
        year: int,
        month: int,
        day: int,
        weekday: int,
        hour: int,
        minute: int,
        second: int,
    ) -> None:
        """
        Set date and time on RTC.
        :param year: Full year (e.g. 2025)
        :param month: Month (1-12)
        :param day: Day of month (1-31)
        :param weekday: Day of week (0-6, 0=Sunday)
        :param hour: Hour (0-23)
        :param minute: Minute (0-59)
        :param second: Second (0-59)
        """
        data = bytearray(7)
        data[0] = self._dec2bcd(second)
        data[1] = self._dec2bcd(minute)
        data[2] = self._dec2bcd(hour)
        data[3] = self._dec2bcd(day)
        data[4] = self._dec2bcd(weekday)
        data[5] = self._dec2bcd(month)
        data[6] = self._dec2bcd(year % 100)
        self.i2c.writeto_mem(self.address, 0x02, data)
