from __future__ import annotations

import argparse
import base64
import html
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from app.config import load_config
from app.conversion_runs import ConversionService
from app.converters.registry import list_converters


CONFIG = load_config()
CONVERSIONS = ConversionService(CONFIG)


def _web_index() -> str:
    return (CONFIG.app_root / "app" / "web" / "index.html").read_text(encoding="utf-8")


def _json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _html_response(handler: BaseHTTPRequestHandler, payload: str) -> None:
    body = payload.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def handle_conversion(payload: dict) -> dict:
    content_base64 = str(payload.get("content_base64") or "")
    content = base64.b64decode(content_base64, validate=True)
    result = CONVERSIONS.create_conversion_run(
        filename=str(payload.get("filename") or "upload.bin"),
        content=content,
        converter_id=str(payload.get("converter_id") or payload.get("converter") or "pymupdf4llm"),
        options=payload.get("options") or {},
    )
    return result.to_api_response()


class Handler(BaseHTTPRequestHandler):
    server_version = "MDWebServerConverters/0.2"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/":
            _html_response(self, _web_index())
        elif path == "/api/converters":
            file_type = (query.get("file_type") or query.get("extension") or [None])[0]
            _json_response(self, {"converters": list_converters(CONFIG, file_type)})
        elif path == "/health":
            _json_response(self, {"status": "ok", "service": "converter"})
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if path == "/api/conversions":
                result = handle_conversion(payload)
                status = 200 if result.get("status") == "success" else 422
                _json_response(self, result, status=status)
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except Exception as exc:  # noqa: BLE001
            _json_response(self, {"error": html.escape(str(exc))}, status=500)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MDWebServer converter service.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8010)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    CONFIG.run_root.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving MDWebServer converter service on http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
