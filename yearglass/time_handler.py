import machine  # type: ignore
import ntptime  # type: ignore
import utime as time  # type: ignore

from .usbprint import usbprint


class TimeHandler:
    def __init__(self, station=None, rtc=None):
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
            t = self.get_rtc_time(local=True)
        if t is None:
            usbprint(
                "[get_year_progress] RTC failed or returned None, using Pico internal time..."
            )
            t = self.get_pico_time(local=True)
        if t is None:
            usbprint("[get_year_progress] Pico internal time failed, returning (0, 0)")
            return (0, 0)
        year, _, _, _, _, _, _, yearday = t

        def _is_leap(y: int) -> bool:
            return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

        total_days = 366 if _is_leap(year) else 365
        # Only fully completed days are elapsed
        days_elapsed = max(0, yearday - 1)
        usbprint(f"[get_year_progress] Year progress: {days_elapsed}/{total_days} days")
        return (days_elapsed, total_days)

    def lightsleep_till_midnight(self) -> None:
        """
        Sleep in light sleep mode in chunks until midnight.
        Sleeps for up to 1 hour at a time, looping until midnight. Skips sleep if no time remains.
        Handles the case where time rolls over past midnight and s_left increases unexpectedly.
        """
        max_lightsleep_ms: int = 3600000  # 1 hour
        s_left: int = self.get_seconds_till_midnight()
        if s_left <= 0:
            usbprint("[safesleep] No time left until midnight, skipping sleep.")
            return
        while s_left > 0:
            ms_left: int = int(s_left * 1000)
            ms_sleep: int = min(ms_left, max_lightsleep_ms)
            usbprint(
                f"[safesleep] Entering lightsleep for {ms_sleep // 1000} s (till midnight: {s_left} s)"
            )
            time.sleep(0.25)  # Add buffer before going to ligtsleep
            machine.lightsleep(ms_sleep)
            new_s_left: int = self.get_seconds_till_midnight()
            if new_s_left > s_left:
                usbprint(
                    f"[safesleep] Detected time rollover or drift: seconds till midnight increased from {s_left} to {new_s_left}. Exiting sleep loop."
                )
                break
            s_left = new_s_left
            if s_left <= 0:
                usbprint("[safesleep] No time left until midnight, skipping sleep.")
                break
            usbprint(
                f"[safesleep] There is still {s_left} s till midnight. Entering lightsleep again."
            )

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
                t = self.get_rtc_time(local=True)
            if t is None:
                t = self.get_pico_time(local=True)
            if t is None:
                fallback_time = 3600
                usbprint(
                    f"[get_seconds_till_midnight] Pico internal time failed, returning fallback {fallback_time} seconds."
                )
                return fallback_time
            _, _, _, hour, minute, second, *_ = t
            seconds_till_midnight: int = (
                (24 - hour - 1) * 3600 + (60 - minute - 1) * 60 + (60 - second)
            )
            if seconds_till_midnight < 0:
                fallback_time = 3600
                usbprint(
                    f"[get_seconds_till_midnight] {fallback_time} seconds until midnight..."
                )
                return fallback_time
            else:
                # Add 60 seconds buffer to ensure refresh happens after midnight, compensating for possible drift
                drift_compensated_time: int = seconds_till_midnight + 60
                usbprint(
                    f"[get_seconds_till_midnight] {drift_compensated_time} seconds until midnight..."
                )
                return drift_compensated_time
        except Exception as e:
            fallback_time = 3600
            usbprint(
                f"[get_seconds_till_midnight] Exception: {e}. Returning fallback {fallback_time} seconds."
            )
            return fallback_time

    def get_time(
        self, local: bool = True, retries: int | None = 2, delay: int = 15
    ) -> tuple | None:
        """
        Try to get time in order: NTP (WiFi) -> RTC -> Pico internal.
        Always stores and updates RTC/Pico in UTC. Only converts to local (Europe/Warsaw) if requested.
        :param local: Return local time (Europe/Warsaw) if True, else UTC
        :param retries: Number of retries for NTP fetch
        :param delay: Delay between retries
        :return: (year, month, mday, hour, minute, second, weekday, yearday)
        """

        # Try NTP (UTC)
        if self.station is not None:
            if self.station.connect():
                t_ntp = self.get_ntp_time(local=False, retries=retries, delay=delay)
                self.station.disconnect()
                self.station.sleep()
                if t_ntp is not None:
                    self._update_rtc_time(t_ntp)
                    self._update_pico_time(t_ntp)
                    if local:
                        t_local = self._make_time_local(t_ntp)
                        usbprint(f"[get_time] NTP: Returning local time: {t_local}")
                        return t_local
                    usbprint(f"[get_time] NTP: Returning UTC time: {t_ntp}")
                    return t_ntp[:8]

        # Try RTC (UTC)
        if self.rtc is not None:
            try:
                t_rtc = self.get_rtc_time(local=False)
                if t_rtc is not None:
                    self._update_pico_time(t_rtc)
                    if local:
                        t_local = self._make_time_local(t_rtc)
                        usbprint(f"[get_time] RTC: Returning local time: {t_local}")
                        return t_local
                    usbprint(f"[get_time] RTC: Returning UTC time: {t_rtc}")
                    return t_rtc[:8]
            except Exception as e:
                usbprint(f"[get_time] RTC failed: {e}")

        # Try Pico (UTC)
        try:
            t_pico = self.get_pico_time(local=False)
            if t_pico is not None:
                if local:
                    t_local = self._make_time_local(t_pico)
                    usbprint(f"[get_time] PICO: Returning local time: {t_local}")
                    return t_local
                usbprint(f"[get_time] PICO: Returning UTC time: {t_pico}")
                return t_pico[:8]
        except Exception as e:
            usbprint(f"[get_time] Unable to get time from Pico: {e}")
            return None

        return None

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
                    usbprint(
                        f"[get_ntp_time] Error fetching time from NTP: {e} (attempt {attempt}/{retries})"
                    )
                else:
                    usbprint(
                        f"[get_ntp_time] Error fetching time from NTP: {e} (attempt {attempt})"
                    )
                if retries is not None and attempt >= retries:
                    usbprint("NTP fetch failed after retries.")
                    return None
                usbprint(f"Retrying NTP fetch in {delay} seconds...")
                time.sleep(delay)
                continue
            break

        t = time.localtime()
        if not local:
            usbprint(f"[get_ntp_time] NTP time (UTC): {t}")
            return t[:8]
        # t is in UTC
        local_t = self._make_time_local(t)
        usbprint(f"[get_ntp_time] NTP time (local): {local_t}")
        return local_t

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
            usbprint(f"[get_rtc_time] Invalid RTC tuple: {e}")
            return None

        t = (year, month, mday, hour, minute, second, weekday, 0)
        try:
            ts = time.mktime(t)
        except Exception as e:
            usbprint(f"[get_rtc_time] mktime failed: {e}")
            return None

        if not local:
            usbprint(f"[get_rtc_time] RTC time (UTC): {t}")
            return time.localtime(ts)[:8]

        local_t = self._make_time_local(time.localtime(ts))
        usbprint(f"[get_rtc_time] RTC time (local): {local_t}")
        return local_t

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
            usbprint(f"[get_pico_time] time.localtime() failed: {e}")
            return None

        if not local:
            usbprint(f"[get_pico_time] Internal time (UTC): {t}")
            return t[:8]

        try:
            local_t = self._make_time_local(t)
            usbprint(f"[get_pico_time] Internal time (local): {local_t}")
            return local_t
        except Exception as e:
            usbprint(f"[get_pico_time] Exception: {e}")
            return None

    def _make_time_local(
        self, t: tuple[int, int, int, int, int, int, int, int]
    ) -> tuple[int, int, int, int, int, int, int, int]:
        """
        Convert a UTC time tuple to Polish local time (Europe/Warsaw), applying DST if needed.
        Expects a tuple matching time.localtime():
            (year, month, mday, hour, minute, second, weekday, yearday)
        Returns a tuple in the same format, but in local time.
        """
        offset = 2 if self._is_dst_poland(t) else 1
        ts = time.mktime(t) + offset * 3600
        local_t = time.localtime(ts)
        return local_t[:8]

    def _is_dst_poland(self, t: tuple[int, int, int, int, int, int, int, int]) -> bool:
        """
        Determine if DST is in effect in Poland for the given UTC time tuple.
        Expects a tuple matching time.localtime():
            (year, month, mday, hour, minute, second, weekday, yearday)
        DST in Poland: from last Sunday in March to last Sunday in October.
        Returns True if DST is in effect, False otherwise.
        """
        if len(t) < 6:
            usbprint("[_is_dst_poland] Tuple too short for DST calculation.")
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
            usbprint(f"[_is_dst_poland] Error finding last Sunday: {e}")
            return False

        # DST starts at 2:00 UTC on last Sunday in March
        try:
            dst_start = time.mktime((year, 3, march_last_sunday, 2, 0, 0, 0, 0))  # type: ignore
            dst_end = time.mktime((year, 10, oct_last_sunday, 1, 0, 0, 0, 0))  # type: ignore
            now = time.mktime((year, month, day, hour, minute, second, 0, 0))  # type: ignore
        except Exception as e:
            usbprint(f"[_is_dst_poland] Error in mktime: {e}")
            return False

        in_dst = dst_start <= now < dst_end
        usbprint(f"[_is_dst_poland] DST in effect: {in_dst}")
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
            usbprint("[TimeHandler] RTC not available, skipping RTC update.")
            return
        if not (isinstance(t, tuple) and len(t) == 8):
            usbprint(f"[TimeHandler] Invalid time tuple for RTC update: {t}")
            return
        try:
            year, month, mday, hour, minute, second, weekday, _ = t
            self.rtc.set_datetime(year, month, mday, weekday, hour, minute, second)
            usbprint(
                f"[TimeHandler] RTC updated to: {year:04d}-{month:02d}-{mday:02d} {hour:02d}:{minute:02d}:{second:02d}"
            )
        except Exception as e:
            usbprint(f"[TimeHandler] Failed to update RTC: {e}")

    def _update_pico_time(
        self, t: tuple[int, int, int, int, int, int, int, int]
    ) -> None:
        """
        Update the Pico internal RTC with the provided time tuple.
        Expects t to be (year, month, mday, hour, minute, second, weekday, yearday).
        Logs success or failure. Validates tuple length and types.
        """
        if not (isinstance(t, tuple) and len(t) == 8):
            usbprint(f"[TimeHandler] Invalid time tuple for Pico update: {t}")
            return
        try:
            year, month, mday, hour, minute, second, _, _ = t
            machine.RTC().datetime((year, month, mday, 0, hour, minute, second, 0))
            usbprint(
                f"[TimeHandler] Pico internal clock updated to: {year:04d}-{month:02d}-{mday:02d} {hour:02d}:{minute:02d}:{second:02d}"
            )
        except Exception as e:
            usbprint(f"[TimeHandler] Failed to update Pico time: {e}")
