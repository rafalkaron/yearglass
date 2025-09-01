from yearglass.rtc import Rtc
from yearglass.time_handler import TimeHandler

try:
    from config import WIFI_PASSWORD, WIFI_SSID  # type: ignore
    from yearglass.wifi import Station
except ImportError:
    WIFI_PASSWORD = None
    WIFI_SSID = None


class TestTimeHandler:
    rtc = Rtc()
    if WIFI_SSID is not None and WIFI_PASSWORD is not None:
        sta = Station(WIFI_SSID, WIFI_PASSWORD)
    else:
        sta = None
    time_handler = TimeHandler(rtc=rtc, station=sta)

    def test_get_year_progress(self):
        days_elapsed, days_total = self.time_handler.get_year_progress()
        print(f"get_year_progress: ({days_elapsed}, {days_total})")
        assert isinstance(days_elapsed, int)
        assert isinstance(days_total, int)
        assert days_total in (365, 366)

    def test_get_seconds_till_midnight(self):
        seconds = self.time_handler.get_seconds_till_midnight()
        print(f"get_seconds_till_midnight: {seconds}")
        assert isinstance(seconds, int)
        assert 0 <= seconds <= 86400

    def test_get_time(self):
        t = self.time_handler.get_time()
        print(f"get_time: {t}")
        assert t is None or (isinstance(t, tuple) and len(t) == 8)

    def test_get_ntp_time(self):
        t = self.time_handler.get_ntp_time()
        print(f"get_ntp_time: {t}")
        assert isinstance(t, tuple)
        assert len(t) == 8

    def test_get_rtc_time(self):
        t = self.time_handler.get_rtc_time()
        print(f"get_rtc_time: {t}")
        assert isinstance(t, tuple)
        assert len(t) == 8

    def test_get_pico_time(self):
        t = self.time_handler.get_pico_time()
        print(f"get_pico_time: {t}")
        assert isinstance(t, tuple)
        assert len(t) == 8

    def test_is_dst_poland(self):
        # Last Sunday of March 2025 is 30th, DST should start at 2:00 UTC
        assert not self.time_handler._is_dst_poland((2025, 3, 29, 12, 0, 0, 0, 0))
        assert self.time_handler._is_dst_poland((2025, 3, 30, 3, 0, 0, 0, 0))
        # Last Sunday of October 2025 is 26th, DST ends at 1:00 UTC
        assert self.time_handler._is_dst_poland((2025, 10, 25, 12, 0, 0, 0, 0))
        assert not self.time_handler._is_dst_poland((2025, 10, 26, 2, 0, 0, 0, 0))

    def test_update_rtc_time(self):
        # Should not raise or update with invalid tuple
        try:
            self.time_handler._update_rtc_time((2025, 8, 28))  # type: ignore Too short
            self.time_handler._update_rtc_time("not a tuple")  # type: ignore Wrong type
        except Exception as e:
            print(f"Exception in test_update_rtc_time_tuple_validation: {e}")
            assert False
        self.time_handler._update_rtc_time((2025, 8, 28, 3, 12, 34, 56, 0))

    def test_update_pico_time(self):
        # Should not raise or update with invalid tuple
        try:
            self.time_handler._update_pico_time((2025, 8, 28))  # type: ignore Too short
            self.time_handler._update_pico_time("not a tuple")  # type: ignore Wrong type
        except Exception as e:
            print(f"Exception in test_update_pico_time_tuple_validation: {e}")
            assert False
        self.time_handler._update_pico_time((2025, 8, 28, 3, 12, 34, 56, 0))

    def run_all(self):
        self.test_get_year_progress()
        self.test_get_seconds_till_midnight()
        self.test_get_time()
        self.test_get_ntp_time()
        self.test_get_rtc_time()
        self.test_get_pico_time()
        self.test_is_dst_poland()
        self.test_update_rtc_time()
        self.test_update_pico_time()


if __name__ == "__main__":
    test = TestTimeHandler()
    test.run_all()
