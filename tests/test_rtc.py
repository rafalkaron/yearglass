import utime  # type: ignore
from machine import I2C, Pin  # type: ignore

from yearglass.rtc import Rtc


class TestRtc:
    def __init__(self):
        self.i2c = I2C(0, scl=Pin(5), sda=Pin(4))
        self.rtc = Rtc(self.i2c)

    def test_scan_i2c(self):
        print("[TEST] Scanning I2C bus on GP4 (SDA), GP5 (SCL)...")
        devices = self.i2c.scan()
        if devices:
            print(f"[TEST] I2C devices found: {[hex(addr) for addr in devices]}")
        else:
            print("[TEST] No I2C devices found.")
        utime.sleep(1)

    def test_set_datetime(self):
        print("[TEST] Setting RTC to 2025-08-28 (Thu) 12:34:56...")
        self.rtc.set_datetime(2025, 8, 28, 4, 12, 34, 56)
        utime.sleep(1)

    def test_get_datetime(self):
        print("[TEST] Reading RTC datetime...")
        dt = self.rtc.get_datetime()
        print(f"[TEST] RTC datetime: {dt}")
        print(
            f"[TEST] Year: {dt[0]}, Month: {dt[1]}, Day: {dt[2]}, Weekday: {dt[3]}, Hour: {dt[4]}, Minute: {dt[5]}, Second: {dt[6]}"
        )
        utime.sleep(1)

    def run_all(self):
        self.test_scan_i2c()
        self.test_set_datetime()
        self.test_get_datetime()
        print("[TEST] RTC test complete.")


if __name__ == "__main__":
    test = TestRtc()
    test.run_all()
