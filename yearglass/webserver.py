import socket


class Webserver:
    def __init__(self, host: str = "0.0.0.0", port: int = 80):
        self.host = host
        self.port = port
        self.html_path = "yearglass/index.html"
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
            request = conn.recv(2048)
            if not request:
                conn.close()
                return False
            request = request.decode("utf-8")
            method, _, *_ = request.split(" ", 2)
            if method == "GET":
                self._handle_get(conn)
                return False
            elif method == "POST":
                self._handle_post(conn, request)
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
        print(f"DEBUG: {fields}")
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

    def _read_html(self) -> str:
        try:
            with open(self.html_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<h1>Error loading page: {e}</h1>"

    def _parse_data(self, data: str) -> dict:
        result = {}
        try:
            pairs = data.split("&")
            for pair in pairs:
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    result[k] = v.replace("+", " ")
        except Exception:
            pass
        return result

    def _update_data(self, fields: dict):
        self.ssid = fields.get("ssid", None)
        self.password = fields.get("wifi-password", None)


if __name__ == "__main__":
    try:
        Webserver().run()
    except (KeyboardInterrupt, Exception) as e:
        print(f"Server stopped: {e}")
