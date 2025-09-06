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


class AccessPoint:
    def __init__(self, essid: str = "yearglass", password: str = "yg-okon1") -> None:
        self.essid: str = essid
        self.password: str = password
        self.ap: None | network.AP_IF = None

    def start(self) -> None:
        try:
            self.ap = network.WLAN(network.AP_IF)
            if self.ap is not None:
                self.ap.config(essid=self.essid, password=self.password)
                self.ap.active(True)
                print("Yearglass IP address:", self.ap.ifconfig()[0])
        except Exception as e:
            print(f"Unable to start access point: {e}")

    def stop(self) -> None:
        if self.ap is not None:
            try:
                self.ap.active(False)
                print("Stopped Access Point...")
            except Exception as e:
                print(f"Unable to stop Access Point: {e}")

    def render_configuration(self) -> str:
        """Render multiline configuration string to display on epaper."""
        try:
            return f"""Configuration


1. Connect to WiFi:
   SSID: {self.essid}
   PASS: {self.password}

2. Open 192.168.4.1

3. Follow instructions
"""
        except Exception as e:
            print(f"Unable to render dynamic configuration screen: {e}")
            return """Configuration
See Yearglass docs."""
