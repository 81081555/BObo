from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from game.engine import GameRuleError
from game.service import RoomManager

ROOT = Path(__file__).parent
WEB_ROOT = ROOT / "web"
manager = RoomManager()


class AppHandler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._json(200, {"ok": True})
            return

        if parsed.path.startswith("/api/rooms/") and parsed.path.endswith("/state"):
            parts = parsed.path.strip("/").split("/")
            room_id = parts[2]
            player_id = parse_qs(parsed.query).get("player_id", [""])[0]
            try:
                state = manager.state(room_id, player_id)
                self._json(200, state)
            except GameRuleError as err:
                self._json(400, {"error": str(err)})
            return

        self._serve_static(parsed.path)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        body = self._read_json()
        try:
            if parsed.path == "/api/rooms":
                created = manager.create_room(
                    name=body.get("name", ""),
                    secret=body["secret"],
                    nonce=body.get("nonce", ""),
                    yellow_hint_enabled=bool(body.get("yellow_hint_enabled", False)),
                )
                created["share_url"] = f"/?room={created['room_id']}"
                self._json(201, created)
                return

            if parsed.path.startswith("/api/rooms/") and parsed.path.endswith("/join"):
                room_id = parsed.path.strip("/").split("/")[2]
                joined = manager.join_room(
                    room_id=room_id,
                    name=body.get("name", ""),
                    secret=body["secret"],
                    nonce=body.get("nonce", ""),
                )
                self._json(200, joined)
                return

            if parsed.path.startswith("/api/rooms/") and parsed.path.endswith("/guess"):
                room_id = parsed.path.strip("/").split("/")[2]
                manager.stage_guess(room_id, body["player_id"], body["guess"])
                self._json(200, {"accepted": True})
                return

            self._json(404, {"error": "not found"})
        except KeyError as err:
            self._json(400, {"error": f"missing field: {err.args[0]}"})
        except GameRuleError as err:
            self._json(400, {"error": str(err)})

    def _serve_static(self, path: str) -> None:
        clean = "/index.html" if path in ("/", "") else path
        file_path = (WEB_ROOT / clean.lstrip("/")).resolve()
        if WEB_ROOT.resolve() not in file_path.parents and file_path != WEB_ROOT.resolve():
            self.send_error(404)
            return
        if not file_path.exists() or file_path.is_dir():
            self.send_error(404)
            return

        content = file_path.read_bytes()
        ctype = "text/plain; charset=utf-8"
        if file_path.suffix == ".html":
            ctype = "text/html; charset=utf-8"
        elif file_path.suffix == ".js":
            ctype = "application/javascript; charset=utf-8"
        elif file_path.suffix == ".css":
            ctype = "text/css; charset=utf-8"
        elif file_path.suffix == ".webmanifest":
            ctype = "application/manifest+json; charset=utf-8"

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def run() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 8000), AppHandler)
    print("Listening on http://0.0.0.0:8000")
    server.serve_forever()


if __name__ == "__main__":
    run()
