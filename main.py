import urandom  # type: ignore
import utime  # type: ignore

from yearglass.buttons import Buttons
from yearglass.epaper import EPaper
from yearglass.led import Led
from yearglass.rtc import Rtc
from yearglass.time_handler import TimeHandler
from yearglass.time_visualizer import TimeVisualizer

try:
    from config import WIFI_PASSWORD, WIFI_SSID  # type: ignore
    from yearglass.wifi import Station
except ImportError:
    WIFI_PASSWORD = None
    WIFI_SSID = None


class Yearglass:
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
        try:
            self.rtc = Rtc()
        except Exception as e:
            print(f"[Yearglass] Could not initialize Rtc: {e}")
            self.led.blink_on(3)
            self.rtc = None

        # Handlers
        self.time_handler = TimeHandler(station=self.sta, rtc=self.rtc)
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
        self.seconds_till_midnight: int = 1
        self.current_display_mode: str = "crossout"

    def display_mode(self, mode: str) -> None:
        try:
            # NOTE: display mode methods must be named render_<mode>
            print(f"[display_{mode}] Displaying {mode} progress...")
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
                print(f"[display_mode] Unknown mode: {mode}")
            self.buttons.enable_interrupts()
            self.led.off()
        except Exception as e:
            self.led.blink_on(2)
            print(f"[display_mode] Could not change display mode: {e}")

    def display_next_mode(self):
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
            print(f"[display_next_mode] Could not display next mode: {e}")

    def display_previous_mode(self):
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
            print(f"[display_next_mode] Could not display previous mode: {e}")

    def display_random_mode(self):
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
            print(f"[display_random_mode] Could not display random mode: {e}")

    def display_refresh_current_mode(self):
        try:
            self.led.on()
            if self.current_display_mode in self.display_modes:
                mode = self.current_display_mode
            else:
                mode = self.display_modes[0]
                print(
                    "[display_refresh_curent_mode] No last mode set, displaying the first one"
                )
            self.display_mode(mode)
            self.led.off()
        except Exception as e:
            self.led.blink_on(2)
            print(f"[display_refresh_current_mode] Could not refresh current mode {e}")

    def update_data(self):
        try:

            def fetch_time():
                t: tuple | None = self.time_handler.get_time()
                if t is not None:
                    timestamp: str = self.time_visualizer.render_time_str(t)
                    print(f"[update_data] Updated data at: {timestamp}")
                else:
                    print("[update_data] Unable to fetch time.")

            self.led.blink_off()
            self.led.on()
            self.buttons.disable_interrupts()
            fetch_time()
            self.days_elapsed, self.days_total = self.time_handler.get_year_progress()
            self.buttons.enable_interrupts()
            self.led.off()
        except Exception as e:
            self.led.blink_on(1)
            print(f"[update_data] Failed to update data: {e}")


def main():
    try:
        yearglass: Yearglass = Yearglass()
        while True:
            yearglass.update_data()
            yearglass.display_refresh_current_mode()
            utime.sleep(yearglass.time_handler.get_seconds_till_midnight())
    except Exception as e:
        try:
            yearglass.led.blink_on(0.5)
        except Exception:
            pass
        print(f"[main] Error: {e}")


if __name__ == "__main__":
    main()
