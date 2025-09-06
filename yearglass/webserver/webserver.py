import os
import socket


class Webserver:
    def __init__(self, host: str = "0.0.0.0", port: int = 80):
        self.host = host
        self.port = port
        self.html_index = "yearglass/webserver/index.html"
        self.html_applied = "yearglass/webserver/applied.html"
        self.ssid = None
        self.password = None

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
        html = self._read_html()
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
        html = """
        <html><body><h1>Settings saved!</h1><p>You may now close this page.</p></body></html>
        """
        self._send_response(conn, "200 OK", "text/html", html)

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

    def _read_html(self) -> str:
        try:
            with open(self.html_index, "r") as f:
                return f.read()
        except Exception as e:
            return f"<h1>Error loading page: {e}</h1>"

    def _parse_data(self, data: str) -> dict:
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
        self.ssid = fields.get("ssid", None)
        self.password = fields.get("wifi-password", None)

        config_path = "config.py"
        config_content = (
            f"WIFI_SSID = '{self.ssid}'\nWIFI_PASSWORD = '{self.password}'\n"
        )
        try:
            try:
                os.stat(config_path)
                # File exists, overwrite
                with open(config_path, "w") as f:
                    f.write(config_content)
                    print("Updated config file.")
            except OSError:
                # File does not exist, create
                with open(config_path, "w") as f:
                    f.write(config_content)
                    print("Created new config file.")
        except Exception as e:
            print(f"Failed to save config: {e}")


if __name__ == "__main__":
    try:
        Webserver().run()
    except (KeyboardInterrupt, Exception) as e:
        print(f"Server stopped: {e}")
