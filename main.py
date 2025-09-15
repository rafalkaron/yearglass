import machine  # type: ignore
import urandom  # type: ignore
import utime  # type: ignore

from yearglass.buttons import Buttons
from yearglass.epaper import EPaper
from yearglass.led import Led
from yearglass.rtc import Rtc
from yearglass.time_handler import TimeHandler
from yearglass.time_visualizer import TimeVisualizer
from yearglass.usbprint import usbprint
from yearglass.webserver import Webserver
from yearglass.wifi import AccessPoint, Station


class Yearglass:
    def __init__(self) -> None:
        # Startup delay for power stability
        utime.sleep(2)

        # Hardware initialization
        self.led = Led("LED")
        self.epd = EPaper()
        self.buttons = Buttons(
            key1_pin=15,
            key2_pin=17,
            key3_pin=2,
            on_key1=self.display_next_mode,
            on_key1_long=self.display_refresh_current_mode,
            on_key2=self.display_random_mode,
            on_key2_long=self.update_data,
            on_key3=self.display_previous_mode,
            on_key3_long=self.display_configuration,
        )

        # Hardware configuration
        self.webserver = Webserver()
        self.ap = AccessPoint()
        self.sta = None
        self._configure_wifi()
        self._configure_rtc()

        # Handlers initialization
        self.time_handler = TimeHandler(station=self.sta, rtc=self.rtc)
        self.time_visualizer = TimeVisualizer(
            max_cols=self.epd.max_columns,
            max_rows=self.epd.max_rows,
        )

        # Data initialization
        self.days_elapsed: int = 0
        self.days_total: int = 0
        self.display_modes = [
            "crossout",
            "hourglass",
            "level",
            "spiral",
            "piechart",
        ]
        self.current_display_mode: str = "crossout"

    def _configure_wifi(self) -> None:
        """Configure WiFi with credentials from config.py.
        If config.py does not exit, run prompt user for credentials."""
        try:
            from config import WIFI_PASSWORD, WIFI_SSID  # type: ignore
        except ImportError:
            WIFI_PASSWORD = None
            WIFI_SSID = None

        if WIFI_SSID is not None and WIFI_PASSWORD is not None:
            self.sta = Station(WIFI_SSID, WIFI_PASSWORD)
        else:
            try:
                self.display_configuration(initial=True)
            except Exception as e:
                usbprint(f"[Yearglass] Unable to complete configuration: {e}")

    def _configure_rtc(self) -> None:
        """Configure RTC module if present."""
        try:
            self.rtc = Rtc()
        except Exception as e:
            usbprint(f"[Yearglass] Could not initialize RTC: {e}")
            self.led.blink_on(3)
            self.rtc = None

    def display_configuration(self, initial: bool = False) -> None:
        """Display configuration screen to prompt user to open web interface."""
        self.led.on()
        self.buttons.disable_interrupts()
        self.ap.start()
        self.epd.display_text_rows(self.ap.render_configuration())
        self.webserver.run()
        if (
            self.webserver.wifi_ssid is not None
            and self.webserver.wifi_password is not None
        ):
            self.sta = Station(self.webserver.wifi_ssid, self.webserver.wifi_password)
        else:
            self.sta = None
        self.ap.stop()
        self.time_handler = TimeHandler(station=self.sta, rtc=self.rtc)
        self.buttons.enable_interrupts()
        self.led.off()
        if not initial:
            self.display_refresh_current_mode()

    def display_mode(self, mode: str) -> None:
        """Display year progress mode based on string provided."""
        try:
            # NOTE: display mode methods must be named render_<mode>
            usbprint(f"[display_{mode}] Displaying {mode} progress...")
            self.led.on()
            self.buttons.disable_interrupts()
            self.current_display_mode = mode
            method_name = f"render_{mode}"
            render_func = getattr(self.time_visualizer, method_name, None)
            if render_func is not None:
                result: str = render_func(
                    days_elapsed=self.days_elapsed,
                    days_total=self.days_total,
                )
                self.epd.display_text_rows(result)
            else:
                usbprint(f"[display_mode] Unknown mode: {mode}")
            self.buttons.enable_interrupts()
            self.led.off()
        except Exception as e:
            self.led.blink_on(2)
            usbprint(f"[display_mode] Could not change display mode: {e}")

    def display_next_mode(self):
        """Display next year progress mode."""
        try:
            self.led.on()
            idx = (
                self.display_modes.index(self.current_display_mode)
                if self.current_display_mode in self.display_modes
                else -1
            )
            next_idx = (idx + 1) % len(self.display_modes)
            self.display_mode(self.display_modes[next_idx])
            self.led.off()
        except Exception as e:
            self.led.blink_on(2)
            usbprint(f"[display_next_mode] Could not display next mode: {e}")

    def display_previous_mode(self):
        """Display previous year progress mode."""
        try:
            self.led.on()
            idx = (
                self.display_modes.index(self.current_display_mode)
                if self.current_display_mode in self.display_modes
                else 0
            )
            prev_idx = (idx - 1) % len(self.display_modes)
            self.display_mode(self.display_modes[prev_idx])
            self.led.off()
        except Exception as e:
            self.led.blink_on(2)
            usbprint(f"[display_next_mode] Could not display previous mode: {e}")

    def display_random_mode(self):
        """Display random year progress mode."""
        try:
            self.led.on()
            if self.current_display_mode in self.display_modes:
                current_idx = self.display_modes.index(self.current_display_mode)
                n = len(self.display_modes)
                # Exclude current, previous, and next indices (with wrap-around)
                exclude = {current_idx, (current_idx - 1) % n, (current_idx + 1) % n}
                available = [i for i in range(n) if i not in exclude]
                # If all modes are excluded (e.g., only 1-3 modes), fall back to just excluding current
                if not available:
                    available = [i for i in range(n) if i != current_idx]
            else:
                available = list(range(len(self.display_modes)))
            rand_idx = available[urandom.getrandbits(8) % len(available)]
            self.display_mode(self.display_modes[rand_idx])
            self.led.off()
        except Exception as e:
            self.led.blink_on(2)
            usbprint(f"[display_random_mode] Could not display random mode: {e}")

    def display_refresh_current_mode(self):
        """Refresh current year progress mode. It is needed to display updated data."""
        try:
            self.led.on()
            if self.current_display_mode in self.display_modes:
                mode = self.current_display_mode
            else:
                mode = self.display_modes[0]
                usbprint(
                    "[display_refresh_curent_mode] No last mode set, displaying the first one"
                )
            self.display_mode(mode)
            self.led.off()
        except Exception as e:
            self.led.blink_on(2)
            usbprint(
                f"[display_refresh_current_mode] Could not refresh current mode {e}"
            )

    def update_data(self):
        """Fetch time to update elapsed days and totay days this year."""
        try:

            def fetch_time():
                t: tuple | None = self.time_handler.get_time()
                if t is not None:
                    timestamp: str = self.time_visualizer.render_time_str(t)
                    usbprint(f"[update_data] Updated data at: {timestamp}")
                else:
                    usbprint("[update_data] Unable to fetch time.")

            self.led.blink_off()
            self.led.on()
            self.buttons.disable_interrupts()
            fetch_time()
            self.days_elapsed, self.days_total = self.time_handler.get_year_progress()
            self.buttons.enable_interrupts()
            self.led.off()
        except Exception as e:
            self.led.blink_on(1)
            usbprint(f"[update_data] Failed to update data: {e}")

    def safesleep(self) -> None:
        """
        Sleep in light sleep mode in chunks until midnight.
        Sleeps for up to 1 hour at a time, looping until midnight. Skips sleep if no time remains.
        """
        self.led.on()
        max_lightsleep_ms: int = 3600000  # 1 hour
        s_left: int = self.time_handler.get_seconds_till_midnight()
        if s_left <= 0:
            usbprint("[safesleep] No time left until midnight, skipping sleep.")
            return
        while s_left > 0:
            ms_left: int = int(s_left * 1000)
            ms_sleep: int = min(ms_left, max_lightsleep_ms)
            usbprint(
                f"[safesleep] Entering lightsleep for {ms_sleep // 1000} s (till midnight: {s_left} s)"
            )
            self.led.off()
            machine.lightsleep(ms_sleep)
            s_left = self.time_handler.get_seconds_till_midnight()
            if s_left <= 0:
                usbprint("[safesleep] No time left until midnight, skipping sleep.")
                break
            usbprint(
                f"[safesleep] There is still {s_left} s till midnight. Entering lightsleep again."
            )


def main():
    try:
        yearglass: Yearglass = Yearglass()
        while True:
            yearglass.update_data()
            yearglass.display_refresh_current_mode()
            yearglass.safesleep()

    except Exception as e:
        try:
            yearglass.led.blink_on(0.5)
        except Exception:
            pass
        usbprint(f"[main] Error: {e}")


if __name__ == "__main__":
    main()
