from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from game.engine import GameRuleError
from game.service import RoomManager

ROOT = Path(__file__).parent
WEB_ROOT = ROOT / "web"
manager = RoomManager()


def resolve_static_file(path: str) -> Path | None:
    # SPA fallback: direct open of share path like /room/<id> should return index.html.
    clean = "/index.html" if path in ("/", "") else path
    requested = (WEB_ROOT / clean.lstrip("/")).resolve()
    web_root = WEB_ROOT.resolve()

    if web_root not in requested.parents and requested != web_root:
        return None

    if requested.exists() and requested.is_file():
        return requested

    # Client-side route fallback (no extension): serve index instead of 404.
    if Path(clean).suffix == "":
        return web_root / "index.html"

    return None


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

    def _handle_get_like(self, head_only: bool = False) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            body = json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            if not head_only:
                self.wfile.write(body)
            return

        if parsed.path.startswith("/api/rooms/") and parsed.path.endswith("/state"):
            parts = parsed.path.strip("/").split("/")
            room_id = parts[2]
            player_id = parse_qs(parsed.query).get("player_id", [""])[0]
            try:
                body = json.dumps(manager.state(room_id, player_id), ensure_ascii=False).encode("utf-8")
                self.send_response(200)
            except GameRuleError as err:
                body = json.dumps({"error": str(err)}, ensure_ascii=False).encode("utf-8")
                self.send_response(400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            if not head_only:
                self.wfile.write(body)
            return

        self._serve_static(parsed.path, head_only=head_only)

    def do_GET(self) -> None:  # noqa: N802
        self._handle_get_like(head_only=False)

    def do_HEAD(self) -> None:  # noqa: N802
        self._handle_get_like(head_only=True)

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
                created["share_url"] = f"/room/{created['room_id']}"
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



    def _serve_static(self, path: str, head_only: bool = False) -> None:
        file_path = resolve_static_file(path)
        if file_path is None:
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
        if not head_only:
            self.wfile.write(content)


def run() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Listening on http://{host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    run()
