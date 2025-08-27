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

    def get_gnss_time(
        self, uart, local: bool = True, retries: int | None = 5, delay: int = 1
    ) -> tuple:
        """
        Fetch current UTC time from a GNSS module via UART and convert to Polish local time (Europe/Warsaw),
        including DST adjustment if local=True.
        Retries GNSS fetch on failure.
        If retries is None, retry indefinitely until successful.
        Returns (year, month, mday, hour, minute, second, weekday, yearday)
        If local=False, returns UTC time tuple.
        :param uart: UART object connected to GNSS module
        :param retries: Number of retry attempts for GNSS fetch. If None, retry indefinitely.
        :param delay: Delay between retries (seconds)
        """
        attempt = 0
        while True:
            try:
                attempt += 1
                # Flush input buffer
                while uart.any():
                    uart.read()
                # Wait for a valid GPRMC sentence
                timeout = 5
                t0 = time.time()
                gnss_time = None
                while time.time() - t0 < timeout:
                    line = uart.readline()
                    if not line:
                        continue
                    try:
                        line = line.decode()
                    except Exception:
                        continue
                    if line.startswith("$GPRMC"):
                        # Example: $GPRMC,hhmmss.sss,A,lat,N,lon,E,speed,track,date,magvar,E*cs\r\n
                        # Extract time and date
                        fields = line.strip().split(",")
                        if len(fields) < 10:
                            continue
                        if fields[2] != "A":
                            continue  # Data invalid
                        time_str = fields[1]
                        date_str = fields[9]
                        if not time_str or not date_str:
                            continue
                        # Parse time
                        hour = int(time_str[0:2])
                        minute = int(time_str[2:4])
                        second = int(time_str[4:6])
                        # Parse date
                        day = int(date_str[0:2])
                        month = int(date_str[2:4])
                        year = 2000 + int(date_str[4:6])
                        # Compose UTC time tuple
                        t = (year, month, day, hour, minute, second, 0, 0)
                        gnss_time = t
                        break
                if gnss_time is None:
                    raise Exception("No valid GPRMC sentence received from GNSS")
                break
            except Exception as e:
                if retries is not None:
                    print(
                        f"[get_gnss_time] Error fetching time from GNSS: {e} (attempt {attempt}/{retries})"
                    )
                else:
                    print(
                        f"[get_gnss_time] Error fetching time from GNSS: {e} (attempt {attempt})"
                    )
                if retries is not None and attempt >= retries:
                    print("GNSS fetch failed after retries.")
                    break
                print(f"Retrying GNSS fetch in {delay} seconds...")
                time.sleep(delay)
        if gnss_time is None:
            # Fallback: return internal time
            print("[get_gnss_time] Returning internal time as fallback.")
            t = time.localtime()
        else:
            t = gnss_time
        # Calculate weekday and yearday
        ts = time.mktime(t)
        t_full = time.localtime(ts)
        if not local:
            print(f"[get_gnss_time] GNSS time (UTC): {t_full}")
            return t_full[:8]
        # t is in UTC
        if self._is_dst_poland(t_full):
            offset = 2  # CEST
        else:
            offset = 1  # CET
        ts_local = ts + offset * 3600
        local_t = time.localtime(ts_local)
        print(f"[get_gnss_time] GNSS time (local): {local_t}")
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
