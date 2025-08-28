from yearglass.time_handler import TimeHandler


class TestTimeHandler:
    time_handler = TimeHandler()

    def test_get_ntp_time(self):
        t = self.time_handler.get_ntp_time()
        print(f"get_ntp_time: {t}")
        assert isinstance(t, tuple)
        assert len(t) == 8

    def test_get_internal_time(self):
        t = self.time_handler.get_pico_time()
        print(f"get_internal_time: {t}")
        assert isinstance(t, tuple)
        assert len(t) == 8

    def test_get_year_progress(self):
        days_elapsed, days_total = self.time_handler.get_year_progress()
        print(f"get_year_progress: ({days_elapsed}, {days_total})")
        assert isinstance(days_elapsed, int)
        assert isinstance(days_total, int)
        assert days_total in (365, 366)

    def test_is_dst_poland(self):
        # Last Sunday of March 2025 is 30th, DST should start at 2:00 UTC
        assert not self.time_handler._is_dst_poland((2025, 3, 29, 12, 0, 0, 0, 0))
        assert self.time_handler._is_dst_poland((2025, 3, 30, 3, 0, 0, 0, 0))
        # Last Sunday of October 2025 is 26th, DST ends at 1:00 UTC
        assert self.time_handler._is_dst_poland((2025, 10, 25, 12, 0, 0, 0, 0))
        assert not self.time_handler._is_dst_poland((2025, 10, 26, 2, 0, 0, 0, 0))

    def test_update_rtc_time_tuple_validation(self):
        # Should not raise or update with invalid tuple
        try:
            self.time_handler._update_rtc_time((2025, 8, 28))  # type: ignore Too short
            self.time_handler._update_rtc_time("not a tuple")  # type: ignore Wrong type
        except Exception as e:
            print(f"Exception in test_update_rtc_time_tuple_validation: {e}")
            assert False

    def test_update_pico_time_tuple_validation(self):
        # Should not raise or update with invalid tuple
        try:
            self.time_handler._update_pico_time((2025, 8, 28))  # type: ignore Too short
            self.time_handler._update_pico_time("not a tuple")  # type: ignore Wrong type
        except Exception as e:
            print(f"Exception in test_update_pico_time_tuple_validation: {e}")
            assert False

    def run_all(self):
        self.test_get_year_progress()
        self.test_get_internal_time()
        self.test_get_ntp_time()
        self.test_is_dst_poland()
        self.test_update_rtc_time_tuple_validation()
        self.test_update_pico_time_tuple_validation()


if __name__ == "__main__":
    test = TestTimeHandler()
    test.run_all()
