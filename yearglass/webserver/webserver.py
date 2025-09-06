import os
import socket

import utime as time  # type: ignore


class Webserver:
    def __init__(self, host: str = "0.0.0.0", port: int = 80):
        self.host = host
        self.port = port
        self.html_index: str = "yearglass/webserver/index.html"
        self.html_applied: str = "yearglass/webserver/applied.html"
        self.config: str = "config.py"
        self.wifi_ssid: str | None = None
        self.wifi_password: str | None = None

    def run(self) -> None:
        """Start the webserver and handle requests until a POST is received."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(1)
        print(f"Webserver running on http://{self.host}:{self.port}")
        try:
            while True:
                try:
                    conn, _ = s.accept()
                    should_stop = self.handle_request(conn)
                    if should_stop:
                        break
                except Exception as e:
                    print(f"Webserver accept error: {e}")
        except Exception as e:
            print(f"Webserver error: {e}")
        finally:
            s.close()

    def handle_request(self, conn: socket.socket) -> bool:
        """Handle a single HTTP request. Returns True if server should stop (after POST)."""
        try:
            request = b""
            while True:
                chunk = conn.recv(2048)
                if not chunk:
                    break
                request += chunk
                if b"\r\n\r\n" in request:
                    break
            if not request:
                conn.close()
                return False
            request_str = request.decode("utf-8")
            method, _, *_ = request_str.split(" ", 2)
            if method == "GET":
                self._handle_get(conn)
                return False
            elif method == "POST":
                # Parse headers to get Content-Length
                headers, _, rest = request_str.partition("\r\n\r\n")
                content_length = 0
                for line in headers.split("\r\n"):
                    if line.lower().startswith("content-length:"):
                        try:
                            content_length = int(line.split(":", 1)[1].strip())
                        except Exception:
                            content_length = 0
                        break
                body = rest.encode("utf-8")
                # If not all body bytes received, read the rest
                to_read = content_length - len(body)
                while to_read > 0:
                    chunk = conn.recv(to_read)
                    if not chunk:
                        break
                    body += chunk
                    to_read -= len(chunk)
                # Now handle POST with full request (headers + body)
                full_request = headers + "\r\n\r\n" + body.decode("utf-8")
                self._handle_post(conn, full_request)
                return True
            else:
                self._send_response(
                    conn,
                    "405 Method Not Allowed",
                    "text/html",
                    "<h1>405 Method Not Allowed</h1>",
                )
                return False
        except Exception as e:
            error_html = f"<h1>Internal server error: {e}</h1>"
            self._send_response(
                conn, "500 Internal Server Error", "text/html", error_html
            )
            return False
        finally:
            conn.close()

    def _handle_get(self, conn: socket.socket) -> None:
        """Serve the configuration HTML page."""
        html = self._read_html(self.html_index)
        self._send_response(conn, "200 OK", "text/html", html)

    def _handle_post(self, conn: socket.socket, request: str) -> None:
        """Handle form submission, validate, update, and respond."""

        body = request.split("\r\n\r\n", 1)[-1]
        fields = self._parse_data(body)
        if not self._validate_fields(fields):
            self._send_response(
                conn, "400 Bad Request", "text/html", "<h1>Invalid input</h1>"
            )
            return
        self._update_data(fields)
        # Mask password in log
        pw_log = (
            "*" * len(fields.get("wifi-password", ""))
            if fields.get("wifi-password")
            else ""
        )
        print(f"Received config: ssid={fields.get('ssid', '')}, wifi-password={pw_log}")
        html = self._read_html(self.html_applied)
        self._send_response(conn, "200 OK", "text/html", html)
        # Give the client time to receive the response before closing
        time.sleep(1)

    def _send_response(
        self, conn: socket.socket, status: str, content_type: str, body: str
    ) -> None:
        """Send an HTTP response with proper headers."""
        body_bytes = body.encode()
        headers = (
            f"HTTP/1.1 {status}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body_bytes)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )
        conn.sendall(headers.encode() + body_bytes)

    def _validate_fields(self, fields: dict) -> bool:
        """Validate POSTed form fields."""
        ssid = fields.get("ssid", "")
        password = fields.get("wifi-password", "")
        # Basic validation: non-empty
        return bool(ssid and password)

    def _read_html(self, html_path: str) -> str:
        try:
            with open(html_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<h1>Error loading page: {e}</h1>"

    def _parse_data(self, data: str) -> dict:
        """
        Parse URL-encoded form data into a dictionary.

        Args:
            data: The URL-encoded string from the POST body.

        Returns:
            A dictionary mapping form field names to their decoded values.
        """
        result = {}
        try:
            pairs = data.strip().split("&")
            for pair in pairs:
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    # Replace + with space, then percent-decode
                    k = k.replace("+", " ")
                    v = v.replace("+", " ")
                    k = self._percent_decode(k)
                    v = self._percent_decode(v)
                    result[k] = v
        except Exception:
            pass
        return result

    def _percent_decode(self, s: str) -> str:
        """
        Decode percent-encoded characters in a string (e.g., 'abc%20def' -> 'abc def').

        Args:
            s: The percent-encoded string.

        Returns:
            The decoded string with percent-encoded sequences replaced by their character equivalents.
        """
        res = ""
        i = 0
        while i < len(s):
            if s[i] == "%" and i + 2 < len(s):
                try:
                    res += chr(int(s[i + 1 : i + 3], 16))
                    i += 3
                except Exception:
                    res += s[i]
                    i += 1
            else:
                res += s[i]
                i += 1
        return res

    def _update_data(self, fields: dict):
        """Update webserver attributes and config file."""
        self.wifi_ssid = fields.get("ssid", None)
        self.wifi_password = fields.get("wifi-password", None)

        config_content = (
            f"WIFI_SSID = '{self.wifi_ssid}'\nWIFI_PASSWORD = '{self.wifi_password}'\n"
        )
        try:
            try:
                os.stat(self.config)
                with open(self.config, "w") as f:
                    f.write(config_content)
                    print("[_update_data] Updated config file.")
            except OSError:
                with open(self.config, "w") as f:
                    f.write(config_content)
                    print("[_update_data] Created new config file.")
        except Exception as e:
            print(f"Failed to save config: {e}")
