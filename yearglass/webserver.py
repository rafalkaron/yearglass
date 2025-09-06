import os
import socket


class Webserver:
    def __init__(self, host: str = "0.0.0.0", port: int = 80):
        self.host = host
        self.port = port
        self.html_path = os.path.join(os.path.dirname(__file__), "configuration.html")

        self.ssid: str | None = None
        self.password: str | None = None
        self.timezone: str | None = None

    def run(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(1)
            print(f"Webserver running on http://{self.host}:{self.port}")
            while True:
                conn, _ = s.accept()
                try:
                    self.handle_request(conn)
                finally:
                    conn.close()
        except Exception as e:
            print(f"Webserver error: {e}")
        finally:
            s.close()

    def handle_request(self, conn):
        try:
            request = conn.recv(2048)
            if not request:
                return
            request = request.decode("utf-8", errors="ignore")
            method, _, *_ = request.split(" ", 2)
            if method == "GET":
                html = self._read_html()
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html
                conn.sendall(response.encode())
            elif method == "POST":
                body = request.split("\r\n\r\n", 1)[-1]
                fields = self._parse_data(body)
                self._update_data(fields)

            else:
                response = "HTTP/1.1 405 Method Not Allowed\r\n\r\n"
                conn.sendall(response.encode())
        except Exception as e:
            error_html = f"<h1>Internal server error: {e}</h1>"
            response = (
                "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n"
                + error_html
            )
            try:
                conn.sendall(response.encode())
            except Exception:
                pass

    def _read_html(self) -> str:
        try:
            with open(self.html_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"<h1>Error loading configuration page: {e}</h1>"

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
        self.timezone = fields.get("timezone", "0")


if __name__ == "__main__":
    Webserver().run()
