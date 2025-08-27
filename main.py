import urandom  # type: ignore
import utime  # type: ignore

from yearglass.buttons import Buttons
from yearglass.epaper import EPaper
from yearglass.led import Led
from yearglass.gnss import Gnss
from yearglass.time_handler import TimeHandler
from yearglass.time_visualizer import TimeVisualizer

try:
    from config import WIFI_PASSWORD, WIFI_SSID
    from yearglass.wifi import Station
except ImportError:
    WIFI_PASSWORD = None
    WIFI_SSID = None


class YearGlass:
    def __init__(self) -> None:
        # Startup delay for power stability
        utime.sleep(2)
        # Hardware
        if WIFI_SSID is not None and WIFI_PASSWORD is not None:
            self.sta = Station(WIFI_SSID, WIFI_PASSWORD)
        else:
            self.sta = None
        self.led = Led("LED")
        self.epd = EPaper()
        self.buttons = Buttons(
            key1_pin=15,
            key2_pin=17,
            key3_pin=2,
            on_key1=self.display_next_mode,
            on_key2=self.display_random_mode,
            on_key3=self.display_previous_mode,
        )
        self.gnss = Gnss()

        # Handlers
        self.time_handler = TimeHandler()
        self.time_visualizer = TimeVisualizer(
            max_cols=self.epd.max_columns,
            max_rows=self.epd.max_rows,
        )

        # Data
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

    def display_mode(self, mode: str) -> None:
        # NOTE: display mode methods must be named render_<mode>
        print(f"[display_{mode}] Displaying {mode} progress...")
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
            print(f"[display_mode] Unknown mode: {mode}")
        self.buttons.enable_interrupts()

    def display_next_mode(self):
        idx = (
            self.display_modes.index(self.current_display_mode)
            if self.current_display_mode in self.display_modes
            else -1
        )
        next_idx = (idx + 1) % len(self.display_modes)
        self.display_mode(self.display_modes[next_idx])

    def display_previous_mode(self):
        idx = (
            self.display_modes.index(self.current_display_mode)
            if self.current_display_mode in self.display_modes
            else 0
        )
        prev_idx = (idx - 1) % len(self.display_modes)
        self.display_mode(self.display_modes[prev_idx])

    def display_random_mode(self):
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

    def display_refresh_current_mode(self):
        if self.current_display_mode in self.display_modes:
            mode = self.current_display_mode
        else:
            mode = self.display_modes[0]
            print("[update_data] No last mode set, defaulting to the first one")
        self.display_mode(mode)

    def update_data(self):
        self.buttons.disable_interrupts()
        self.led.on()
        if self.sta is not None:
            if self.sta.connect():
                t: tuple = self.time_handler.get_ntp_time()
            else:
                t = self.time_handler.get_internal_time()
        print(f"[update_data] timestamp: {self.time_visualizer.render_time_str(t)}")
        self.days_elapsed, self.days_total = self.time_handler.get_year_progress()
        if self.sta is not None:
            self.sta.disconnect()
            self.sta.sleep()
        self.led.off()
        self.buttons.enable_interrupts()


def main():
    try:
        yg: YearGlass = YearGlass()
        yg.update_data()
        yg.display_refresh_current_mode()
        yg.buttons.enable_interrupts()

        while True:
            seconds_till_midnight: int = yg.time_handler.get_seconds_till_midnight()
            utime.sleep(seconds_till_midnight)
            yg.update_data()
            yg.display_refresh_current_mode()

    except Exception as e:
        try:
            yg.led.on()
        except Exception:
            pass
        print(f"[main] Error: {e}")


if __name__ == "__main__":
    main()
