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
                t = self.get_rtc_time(local=local)
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

    def get_rtc_time(
        self, local: bool = True
    ) -> tuple[int, int, int, int, int, int, int, int] | None:
        """
        Convert RTC tuple (year, month, day, weekday, hour, minute, second)
        to a tuple matching time.localtime():
            (year, month, mday, hour, minute, second, weekday, yearday)
        Applies local offset if needed. Returns None if any error occurs.
        """
        try:
            rtc_tuple = self.rtc.get_datetime()  # type: ignore
            year, month, mday, weekday, hour, minute, second = rtc_tuple
        except Exception as e:
            print(f"[get_rtc_time] Invalid RTC tuple: {e}")
            return None

        t = (year, month, mday, hour, minute, second, weekday, 0)
        try:
            ts = time.mktime(t)
        except Exception as e:
            print(f"[get_rtc_time] mktime failed: {e}")
            return None

        if not local:
            print(f"[get_rtc_time] RTC time (UTC): {t}")
            return time.localtime(ts)[:8]

        offset = 2 if self._is_dst_poland(time.localtime(ts)) else 1
        ts += offset * 3600
        local_t = time.localtime(ts)
        print(f"[get_rtc_time] RTC time (local): {local_t}")
        return local_t[:8]

    def get_pico_time(
        self, local: bool = True
    ) -> tuple[int, int, int, int, int, int, int, int] | None:
        """
        Return the current internal Pi time as a tuple matching time.localtime():
            (year, month, mday, hour, minute, second, weekday, yearday)
        If local=True, convert to Polish local time (Europe/Warsaw) with DST adjustment.
        If local=False, return UTC time tuple. Returns None if any error occurs.
        """
        try:
            t = time.localtime()
        except Exception as e:
            print(f"[get_pico_time] time.localtime() failed: {e}")
            return None

        if not local:
            print(f"[get_pico_time] Internal time (UTC): {t}")
            return t[:8]

        try:
            offset = 2 if self._is_dst_poland(t) else 1
            ts = time.mktime(t) + offset * 3600
            local_t = time.localtime(ts)
            print(f"[get_pico_time] Internal time (local): {local_t}")
            return local_t[:8]
        except Exception as e:
            print(f"[get_pico_time] Exception: {e}")
            return None

    def _is_dst_poland(self, t: tuple[int, int, int, int, int, int, int, int]) -> bool:
        """
        Determine if DST is in effect in Poland for the given UTC time tuple.
        Expects a tuple matching time.localtime():
            (year, month, mday, hour, minute, second, weekday, yearday)
        DST in Poland: from last Sunday in March to last Sunday in October.
        Returns True if DST is in effect, False otherwise.
        """
        if len(t) < 6:
            print("[_is_dst_poland] Tuple too short for DST calculation.")
            return False

        year, month, day, hour, minute, second = t[:6]

        def last_sunday(year: int, month: int) -> int:
            """Return the day of the month for the last Sunday of the given month."""
            for week in range(31, 24, -1):
                try:
                    tm = time.localtime(time.mktime((year, month, week, 1, 0, 0, 0, 0)))  # type: ignore
                    if tm[1] == month and tm[6] == 6:  # Sunday
                        return week
                except Exception:
                    continue
            raise ValueError(f"No Sunday found in {year}-{month}")

        try:
            march_last_sunday = last_sunday(year, 3)
            oct_last_sunday = last_sunday(year, 10)
        except Exception as e:
            print(f"[_is_dst_poland] Error finding last Sunday: {e}")
            return False

        # DST starts at 2:00 UTC on last Sunday in March
        try:
            dst_start = time.mktime((year, 3, march_last_sunday, 2, 0, 0, 0, 0))  # type: ignore
            dst_end = time.mktime((year, 10, oct_last_sunday, 1, 0, 0, 0, 0))  # type: ignore
            now = time.mktime((year, month, day, hour, minute, second, 0, 0))  # type: ignore
        except Exception as e:
            print(f"[_is_dst_poland] Error in mktime: {e}")
            return False

        in_dst = dst_start <= now < dst_end
        print(f"[_is_dst_poland] DST in effect: {in_dst}")
        return in_dst

    def _update_rtc_time(
        self, t: tuple[int, int, int, int, int, int, int, int]
    ) -> None:
        """
        Update the external RTC with the provided time tuple.
        Expects t to be (year, month, mday, hour, minute, second, weekday, yearday).
        Logs success or failure. Validates tuple length and types.
        """
        if self.rtc is None:
            print("[TimeHandler] RTC not available, skipping RTC update.")
            return
        if not (isinstance(t, tuple) and len(t) == 8):
            print(f"[TimeHandler] Invalid time tuple for RTC update: {t}")
            return
        try:
            year, month, mday, hour, minute, second, weekday, _ = t
            self.rtc.set_datetime(year, month, mday, weekday, hour, minute, second)
            print(
                f"[TimeHandler] RTC updated to: {year:04d}-{month:02d}-{mday:02d} {hour:02d}:{minute:02d}:{second:02d}"
            )
        except Exception as e:
            print(f"[TimeHandler] Failed to update RTC: {e}")

    def _update_pico_time(
        self, t: tuple[int, int, int, int, int, int, int, int]
    ) -> None:
        """
        Update the Pico internal RTC with the provided time tuple.
        Expects t to be (year, month, mday, hour, minute, second, weekday, yearday).
        Logs success or failure. Validates tuple length and types.
        """
        if not (isinstance(t, tuple) and len(t) == 8):
            print(f"[TimeHandler] Invalid time tuple for Pico update: {t}")
            return
        try:
            year, month, mday, hour, minute, second, _, _ = t
            machine.RTC().datetime((year, month, mday, 0, hour, minute, second, 0))
            print(
                f"[TimeHandler] Pico internal clock updated to: {year:04d}-{month:02d}-{mday:02d} {hour:02d}:{minute:02d}:{second:02d}"
            )
        except Exception as e:
            print(f"[TimeHandler] Failed to update Pico time: {e}")
