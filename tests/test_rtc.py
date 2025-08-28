import utime  # type: ignore

from yearglass.rtc import Rtc


def main():
    print("[TEST] RTC test starting...")
    rtc = Rtc()

    # Set a known datetime (e.g. 2025-08-28 Thursday 12:34:56)
    print("[TEST] Setting RTC to 2025-08-28 (Thu) 12:34:56...")
    rtc.set_datetime(2025, 8, 28, 4, 12, 34, 56)
    utime.sleep(1)

    print("[TEST] Reading RTC datetime...")
    dt = rtc.get_datetime()
    print(f"[TEST] RTC datetime: {dt}")

    # Optionally, print each field
    print(
        f"[TEST] Year: {dt[0]}, Month: {dt[1]}, Day: {dt[2]}, Weekday: {dt[3]}, Hour: {dt[4]}, Minute: {dt[5]}, Second: {dt[6]}"
    )
    print("[TEST] RTC test complete.")


if __name__ == "__main__":
    main()
