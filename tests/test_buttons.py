import utime  # type: ignore

from yearglass.buttons import Buttons

# Use requested pins
KEY1_PIN = 15
KEY2_PIN = 17
KEY3_PIN = 2


def on_key1():
    print("[TEST] KEY1 callback triggered!")


def on_key2():
    print("[TEST] KEY2 callback triggered!")


def on_key3():
    print("[TEST] KEY3 callback triggered!")


def main():
    print("[TEST] Press each button to test callbacks. Press Ctrl+C to exit.")
    Buttons(KEY1_PIN, KEY2_PIN, KEY3_PIN, on_key1, on_key2, on_key3)
    try:
        while True:
            utime.sleep(1)
    except KeyboardInterrupt:
        print("[TEST] Exiting button test.")


if __name__ == "__main__":
    main()
