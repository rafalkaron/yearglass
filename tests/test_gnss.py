import utime  # type: ignore

from yearglass.gnss import Gnss


def main():
    print("[TEST] GNSS module test starting...")
    gnss = Gnss()

    print("[TEST] Putting GNSS to sleep (wup pin HIGH)...")
    gnss.sleep()
    print(f"[TEST] wup pin value after sleep: {gnss.wup.value()}")
    utime.sleep(2)

    print("[TEST] Waking GNSS (wup pin LOW)...")
    gnss.wake()
    print(f"[TEST] wup pin value after wake: {gnss.wup.value()}")
    utime.sleep(2)

    print("[TEST] GNSS test complete.")


if __name__ == "__main__":
    main()
