import time

import network  # type: ignore


class Station:
    def __init__(self, ssid: str, password: str) -> None:
        self.ssid: str = ssid
        self.password: str = password
        self.sta: network.WLAN | None = None

    def connect(
        self, timeout: int = 5, retries: int | None = 5, delay: int = 15
    ) -> bool:
        """
        Connect to WiFi with retry logic.
        :param timeout: Timeout for each connection attempt (seconds)
        :param retries: Number of retry attempts. If None, retry indefinitely until connected.
        :param delay: Delay between retries (seconds)
        :return: True if connected, False otherwise (only if retries is not None)
        """
        attempt = 0
        while True:
            attempt += 1
            if self.sta is None:
                self.sta = network.WLAN(network.STA_IF)
                self.sta.active(True)  # type: ignore
            if self.sta.isconnected():  # type: ignore
                print("Already connected.")
                return True
            else:
                if retries is not None:
                    print(f"Connecting to WiFi... (attempt {attempt}/{retries})")
                else:
                    print(f"Connecting to WiFi... (attempt {attempt})")
                self.sta.disconnect()  # type: ignore
                self.sta.connect(self.ssid, self.password)  # type: ignore
            start: float = time.time()
            while not self.sta.isconnected():  # type: ignore
                if time.time() - start > timeout:
                    print("Connection timed out")
                    break
                time.sleep(0.5)
            if self.sta.isconnected():  # type: ignore
                print("Connected, IP address:", self.sta.ifconfig()[0])  # type: ignore
                return True
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
            if retries is not None and attempt >= retries:
                print("WiFi connection failed after retries.")
                return False

    def disconnect(self) -> None:
        """
        Disconnect from WiFi but keep the WiFi module active.
        """
        if self.sta is not None:
            print("Disconnecting from WiFi...")
            self.sta.disconnect()
        else:
            print("WiFi module not initialized.")

    def sleep(self) -> None:
        """
        Put the WiFi module into low power mode (turn off radio).
        """
        if self.sta is not None:
            print("Disabling WiFi module (low power mode)...")
            self.sta.active(False)
        else:
            print("WiFi module not initialized.")
