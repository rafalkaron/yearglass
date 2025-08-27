import ntptime  # type: ignore
import utime as time  # type: ignore


class TimeHandler:
    def get_year_progress(self) -> tuple:
        """
        Return a tuple (days_elapsed, days_total) for the current year.
        Only fully completed days are counted as elapsed (current day is not included).
        """
        try:
            year, _, _, _, _, _, _, yearday = self.get_internal_time()
        except Exception as e:
            print(f"[Inky] Failed to get time: {e}")
            year, yearday = 2025, 227  # 2025-08-14 is the 227th day of 2025

        def _is_leap(y: int) -> bool:
            return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

        total_days = 366 if _is_leap(year) else 365
        # Only fully completed days are elapsed
        days_elapsed = max(0, yearday - 1)
        print(f"[get_year_progress] Year progress: {days_elapsed}/{total_days} days")
        return (days_elapsed, total_days)

    def get_seconds_till_midnight(self) -> int:
        t: tuple = self.get_internal_time()
        _, _, _, hour, minute, second, *_ = t

        seconds_till_midnight: int = (
            (24 - hour - 1) * 3600 + (60 - minute - 1) * 60 + (60 - second)
        )

        if seconds_till_midnight < 0:
            fallback_time = 60
            print(
                f"[get_seconds_till_midnight] {fallback_time} seconds until midnight..."
            )
            return fallback_time
        else:
            # Add 60 seconds buffer to ensure refresh happens after midnight, compensating for possible Pico drift
            drift_compensated_time: int = seconds_till_midnight + 60
            print(
                f"[get_seconds_till_midnight] {drift_compensated_time} seconds until midnight..."
            )
            return drift_compensated_time

    def get_internal_time(self, local: bool = True) -> tuple:
        """
        Return the current internal Pi time as a tuple (year, month, mday, hour, minute, second, weekday, yearday).
        If local=True, convert to Polish local time (Europe/Warsaw) with DST adjustment.
        If local=False, return UTC time tuple.
        """
        t = time.localtime()
        if not local:
            print(f"[get_internal_time] Internal time (UTC): {t}")
            return t[:8]
        # t is in UTC
        if self._is_dst_poland(t):
            offset = 2  # CEST
        else:
            offset = 1  # CET
        ts = time.mktime(t) + offset * 3600
        local_t = time.localtime(ts)
        print(f"[get_internal_time] Internal time (local): {local_t}")
        return local_t[:8]

    def get_ntp_time(
        self, local: bool = True, retries: int | None = 5, delay: int = 1
    ) -> tuple:
        """
        Fetch current UTC time from NTP and convert to Polish local time (Europe/Warsaw),
        including DST adjustment if local=True.
        Retries NTP fetch on failure.
        If retries is None, retry indefinitely until successful.
        Returns (year, month, mday, hour, minute, second, weekday, yearday)
        If local=False, returns UTC time tuple.
        :param retries: Number of retry attempts for NTP fetch. If None, retry indefinitely.
        :param delay: Delay between retries (seconds)
        """
        attempt = 0
        while True:
            try:
                attempt += 1
                ntptime.settime()
                break
            except Exception as e:
                if retries is not None:
                    print(
                        f"[get_ntp_time] Error fetching time from NTP: {e} (attempt {attempt}/{retries})"
                    )
                else:
                    print(
                        f"[get_ntp_time] Error fetching time from NTP: {e} (attempt {attempt})"
                    )
                if retries is not None and attempt >= retries:
                    print("NTP fetch failed after retries.")
                    break
                print(f"Retrying NTP fetch in {delay} seconds...")
                time.sleep(delay)
        t = time.localtime()
        if not local:
            return t[:8]
        # t is in UTC
        if self._is_dst_poland(t):
            offset = 2  # CEST
        else:
            offset = 1  # CET
        # Convert to local time
        ts = time.mktime(t) + offset * 3600
        local_t = time.localtime(ts)
        print(f"[get_ntp_time] NTP time (local): {local_t}")
        return local_t[:8]

    def _is_dst_poland(self, t: tuple) -> bool:
        """
        Determine if DST is in effect in Poland for the given UTC time tuple.
        DST in Poland: from last Sunday in March to last Sunday in October.
        """
        year = t[0]
        # Last Sunday in March
        march_last_sunday = max(
            week
            for week in range(31, 24, -1)
            if time.localtime(time.mktime((year, 3, week, 1, 0, 0, 0, 0)))[:3][1] == 3  # type: ignore
        )
        # Last Sunday in October
        oct_last_sunday = max(
            week
            for week in range(31, 24, -1)
            if time.localtime(time.mktime((year, 10, week, 1, 0, 0, 0, 0)))[:3][1] == 10  # type: ignore
        )
        # Unpack only the first 6 elements (year, month, day, hour, minute, second)
        y, m, d, h, mi, s = t[:6]
        # DST starts at 2:00 UTC on last Sunday in March
        dst_start = time.mktime((year, 3, march_last_sunday, 2, 0, 0, 0, 0))  # type: ignore
        # DST ends at 1:00 UTC on last Sunday in October
        dst_end = time.mktime((year, 10, oct_last_sunday, 1, 0, 0, 0, 0))  # type: ignore
        now = time.mktime((y, m, d, h, mi, s, 0, 0))  # type: ignore
        print(f"[get_dst_poland] DST in effect: {dst_start <= now < dst_end}")
        return dst_start <= now < dst_end
