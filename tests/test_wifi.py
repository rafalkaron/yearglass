import time

from yearglass.wifi import Station

try:
    from config import WIFI_PASSWORD, WIFI_SSID  # type: ignore
except ImportError:
    WIFI_PASSWORD = None
    WIFI_SSID = None


def main():
    print("[TEST] WiFi Station test starting...")
    if WIFI_SSID is None or WIFI_PASSWORD is None:
        print("[TEST] No WiFi credentials found in config.py. Exiting test.")
        return
    wifi = Station(WIFI_SSID, WIFI_PASSWORD)

    print("[TEST] Connecting to WiFi...")
    connected = wifi.connect(timeout=5, retries=3, delay=5)
    print(f"[TEST] Connected: {connected}")
    time.sleep(2)

    print("[TEST] Disconnecting from WiFi...")
    wifi.disconnect()
    time.sleep(2)

    print("[TEST] Putting WiFi to sleep...")
    wifi.sleep()
    print("[TEST] Test complete.")


if __name__ == "__main__":
    main()
