import machine  # type: ignore
import ntptime  # type: ignore
import utime as time  # type: ignore


class TimeHandler:
    def __init__(self, gnss=None, station=None, rtc=None):
        self.gnss = gnss
        self.station = station
        self.rtc = rtc

    def get_year_progress(self) -> tuple[int, int]:
        """
        Return a tuple (days_elapsed, days_total) for the current year.
        Only fully completed days are counted as elapsed (current day is not included).
        Tries to get time from RTC, then Pico internal as fallback.
        Handles None from get_rtc_time.
        """
        t = None
        if self.rtc is not None:
            t = self.get_rtc_time(self.rtc.get_datetime(), local=True)
        if t is None:
            print(
                "[get_year_progress] RTC failed or returned None, using Pico internal time..."
            )
            t = self.get_pico_time(local=True)
        if t is None:
            print("[get_year_progress] Pico internal time failed, returning (0, 0)")
            return (0, 0)
        year, _, _, _, _, _, _, yearday = t

        def _is_leap(y: int) -> bool:
            return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

        total_days = 366 if _is_leap(year) else 365
        # Only fully completed days are elapsed
        days_elapsed = max(0, yearday - 1)
        print(f"[get_year_progress] Year progress: {days_elapsed}/{total_days} days")
        return (days_elapsed, total_days)

    def get_seconds_till_midnight(self) -> int:
        """
        Calculate the number of seconds remaining until midnight (local time),
        with a buffer to ensure the refresh happens after midnight.

        Tries to use RTC time first, then falls back to Pico internal time. If both fail,
        returns a fallback value (60 seconds). Adds a 60-second buffer to compensate for
        possible clock drift. Handles exceptions gracefully.

        Returns:
            int: Number of seconds until midnight (plus buffer), or fallback value on error.
        """
        try:
            # Try RTC first, fallback to Pico internal time if None
            t = None
            if self.rtc is not None:
                t = self.get_rtc_time(self.rtc.get_datetime(), local=True)
            if t is None:
                t = self.get_pico_time(local=True)
            if t is None:
                fallback_time = 60
                print(
                    f"[get_seconds_till_midnight] Pico internal time failed, returning fallback {fallback_time} seconds."
                )
                return fallback_time
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
        except Exception as e:
            fallback_time = 60
            print(
                f"[get_seconds_till_midnight] Exception: {e}. Returning fallback {fallback_time} seconds."
            )
            return fallback_time

    def get_time(
        self, local: bool = True, retries: int | None = 2, delay: int = 1
    ) -> tuple | None:
        """
        Try to get time in order: GNSS -> NTP (WiFi) -> RTC -> Pico internal.
        GNSS and NTP will update RTC if successful. If RTC update fails, update Pico time.
        :param local: Return local time (Europe/Warsaw) if True, else UTC
        :param gnss_uart: UART object for GNSS (if needed)
        :param retries: Number of retries for GNSS/NTP fetch
        :param delay: Delay between retries
        :return: (year, month, mday, hour, minute, second, weekday, yearday)
        """

        # 1. Try GNSS
        if self.gnss is not None:
            self.gnss.wake()
            t = self.get_gnss_time(local=local, retries=retries, delay=delay)
            self.gnss.sleep()
            if t is not None:
                self._update_rtc_time(t)
                self._update_pico_time(t)
                return t

        # 2. Try NTP (WiFi)
        if self.station is not None:
            if self.station.connect():
                t = self.get_ntp_time(local=local, retries=retries, delay=delay)
                self.station.disconnect()
                self.station.sleep()
                if t is not None:
                    self._update_rtc_time(t)
                    self._update_pico_time(t)
                    return t

        # 3. Try RTC
        if self.rtc is not None:
            try:
                t = self.get_rtc_time(self.rtc.get_datetime(), local=local)
                if t is not None:
                    self._update_pico_time(t)
                    return t
            except Exception as e:
                print(f"[get_time] RTC failed: {e}")

        # 4. Fallback: Pico internal
        try:
            t = self.get_pico_time(local=local)
            if t is not None:
                return t
        except Exception as e:
            print(f"[get_time] Unable to get time from Pico: {e}")
            return None

    def get_gnss_time(
        self, local: bool = True, retries: int | None = 5, delay: int = 1
    ) -> tuple[int, int, int, int, int, int, int, int] | None:
        """
        Fetch current UTC time from a GNSS module via UART and convert to Polish local time (Europe/Warsaw),
        including DST adjustment if local=True. Retries GNSS fetch on failure.
        If retries is None, retry indefinitely until successful.
        Returns a tuple matching time.localtime():
            (year, month, mday, hour, minute, second, weekday, yearday)
        or None on failure.
        """

        def _parse_gprmc(
            line: str,
        ) -> tuple[int, int, int, int, int, int, int, int] | None:
            fields = line.strip().split(",")
            if len(fields) < 10 or fields[2] != "A":
                return None
            time_str = fields[1]
            date_str = fields[9]
            if not time_str or not date_str:
                return None
            try:
                hour = int(time_str[0:2])
                minute = int(time_str[2:4])
                second = int(time_str[4:6])
                day = int(date_str[0:2])
                month = int(date_str[2:4])
                year = 2000 + int(date_str[4:6])
                return (year, month, day, hour, minute, second, 0, 0)
            except Exception:
                return None

        attempt = 0
        while True:
            attempt += 1
            # Flush input buffer (with a max flush count to avoid infinite loop)
            flush_count = 0
            while self.gnss.uart.any():  # type: ignore
                self.gnss.uart.read()  # type: ignore
                flush_count += 1
                if flush_count > 100:
                    break

            # Wait for a valid GPRMC sentence
            timeout = 5
            t0 = time.time()
            gnss_time = None
            while time.time() - t0 < timeout:
                line = self.gnss.uart.readline()  # type: ignore
                if not line:
                    continue
                try:
                    line = line.decode()
                except Exception:
                    continue
                if line.startswith("$GPRMC"):
                    gnss_time = _parse_gprmc(line)
                    if gnss_time:
                        break
            if not gnss_time:
                if retries is not None:
                    print(
                        f"[get_gnss_time] No valid GPRMC sentence (attempt {attempt}/{retries})"
                    )
                else:
                    print(
                        f"[get_gnss_time] No valid GPRMC sentence (attempt {attempt})"
                    )
                if retries is not None and attempt >= retries:
                    print("GNSS fetch failed after retries.")
                    return None
                print(f"Retrying GNSS fetch in {delay} seconds...")
                time.sleep(delay)
                continue

            # Calculate weekday and yearday
            ts = time.mktime(gnss_time)
            t_full = time.localtime(ts)
            if not local:
                print(f"[get_gnss_time] GNSS time (UTC): {t_full}")
                return t_full[:8]
            # t is in UTC
            offset = 2 if self._is_dst_poland(t_full) else 1
            ts_local = ts + offset * 3600
            local_t = time.localtime(ts_local)
            print(f"[get_gnss_time] GNSS time (local): {local_t}")
            return local_t[:8]

    def get_ntp_time(
        self, local: bool = True, retries: int | None = 5, delay: int = 1
    ) -> tuple[int, int, int, int, int, int, int, int] | None:
        """
        Fetch current UTC time from NTP and convert to Polish local time (Europe/Warsaw),
        including DST adjustment if local=True. Retries NTP fetch on failure.
        If retries is None, retry indefinitely until successful.
        Returns a tuple matching time.localtime():
            (year, month, mday, hour, minute, second, weekday, yearday)
        or None on failure.
        """
        attempt = 0
        while True:
            attempt += 1
            try:
                ntptime.settime()
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
                    return None
                print(f"Retrying NTP fetch in {delay} seconds...")
                time.sleep(delay)
                continue
            break

        t = time.localtime()
        if not local:
            print(f"[get_ntp_time] NTP time (UTC): {t}")
            return t[:8]
        # t is in UTC
        offset = 2 if self._is_dst_poland(t) else 1
        ts = time.mktime(t) + offset * 3600
        local_t = time.localtime(ts)
        print(f"[get_ntp_time] NTP time (local): {local_t}")
        return local_t[:8]

    def get_rtc_time(self, rtc_tuple: tuple, local: bool = True) -> tuple | None:
        """
        Convert RTC tuple (year, month, day, weekday, hour, minute, second)
        to (year, month, mday, hour, minute, second, weekday, yearday)
        and apply local offset if needed. Returns None if any error occurs.
        """
        try:
            year, month, mday, weekday, hour, minute, second = rtc_tuple
            # Compose time tuple for mktime
            t = (year, month, mday, hour, minute, second, weekday, 0)
            ts = time.mktime(t)
            if local:
                if self._is_dst_poland(time.localtime(ts)):
                    offset = 2
                else:
                    offset = 1
                ts += offset * 3600
            local_t = time.localtime(ts)
            return local_t[:8]
        except Exception as e:
            print(f"[get_rtc_time] Exception: {e}")
            return None

    def get_pico_time(self, local: bool = True) -> tuple | None:
        """
        Return the current internal Pi time as a tuple (year, month, mday, hour, minute, second, weekday, yearday).
        If local=True, convert to Polish local time (Europe/Warsaw) with DST adjustment.
        If local=False, return UTC time tuple.
        Returns None if any error occurs.
        """
        try:
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
        except Exception as e:
            print(f"[get_pico_time] Exception: {e}")
            return None

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

    def _update_rtc_time(self, t: tuple) -> None:
        """Try to update RTC with time tuple t."""
        if self.rtc is not None:
            try:
                # t: (year, month, mday, hour, minute, second, weekday, yearday)
                year, month, mday, hour, minute, second, weekday, _ = t
                self.rtc.set_datetime(year, month, mday, weekday, hour, minute, second)
                print("[TimeHandler] RTC updated.")
            except Exception as e:
                print(f"[TimeHandler] Failed to update RTC: {e}")

    def _update_pico_time(self, t: tuple) -> None:
        """Try to update Pico internal clock with time tuple t."""
        try:
            year, month, mday, hour, minute, second, _, _ = t
            machine.RTC().datetime((year, month, mday, 0, hour, minute, second, 0))
            print("[TimeHandler] Pico internal clock updated.")
        except Exception as e:
            print(f"[TimeHandler] Failed to update Pico time: {e}")
