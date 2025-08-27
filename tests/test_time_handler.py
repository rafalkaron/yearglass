from yearglass.time_handler import TimeHandler


class TestTimeHandler:
    time_handler = TimeHandler()

    def test_get_ntp_time(self):
        t = self.time_handler.get_ntp_time()
        print(f"get_ntp_time: {t}")
        assert isinstance(t, tuple)
        assert len(t) == 8

    def test_get_internal_time(self):
        t = self.time_handler.get_internal_time()
        print(f"get_internal_time: {t}")
        assert isinstance(t, tuple)
        assert len(t) == 8

    def test_get_year_progress(self):
        days_elapsed, days_total = self.time_handler.get_year_progress()
        print(f"get_year_progress: ({days_elapsed}, {days_total})")
        assert isinstance(days_elapsed, int)
        assert isinstance(days_total, int)
        assert days_total in (365, 366)

    def run_all(self):
        self.test_get_ntp_time()
        self.test_get_internal_time()
        self.test_get_year_progress()


if __name__ == "__main__":
    test = TestTimeHandler()
    test.run_all()
