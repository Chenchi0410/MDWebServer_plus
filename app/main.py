from __future__ import annotations

import argparse
import base64
import csv
import html
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from app.config import load_config
from app.converters.registry import get_converter, list_converters
from app.evaluations.converter_benchmark import CepingAdapter
from app.evaluations.md_quality import MarkdownQualityEvaluator
from app.schemas.common import new_run_id, utc_now_iso
from app.storage.paths import RunPaths
from app.storage.run_store import write_json


CONFIG = load_config()
RUN_PATHS = RunPaths(CONFIG)
QUALITY = MarkdownQualityEvaluator(CONFIG)
BENCHMARK_SUMMARIES = [
    CONFIG.project_root / "benchmark_runs" / "first_smoke_markitdown" / "reports" / "summary.csv",
    CONFIG.project_root / "benchmark_runs" / "first_smoke_pymupdf4llm" / "reports" / "summary.csv",
]


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


def _safe_filename(filename: str) -> str:
    return Path(filename).name.strip() or "upload.bin"


def benchmark_summary() -> list[dict]:
    grouped: dict[tuple[str, str], dict] = {}
    for summary_path in BENCHMARK_SUMMARIES:
        if not summary_path.exists():
            continue
        with summary_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                converter = row.get("converter", "unknown")
                category = row.get("category", "unknown")
                item = grouped.setdefault(
                    (converter, category),
                    {"converter": converter, "category": category, "total": 0, "success": 0, "scores": []},
                )
                item["total"] += 1
                if row.get("status") == "success":
                    item["success"] += 1
                try:
                    item["scores"].append(float(row.get("overall_score") or 0))
                except ValueError:
                    pass
    rows = []
    for item in grouped.values():
        scores = item.pop("scores")
        item["avg_score"] = round(sum(scores) / len(scores), 4) if scores else None
        rows.append(item)
    return sorted(rows, key=lambda r: (r["converter"], r["category"]))


def handle_conversion(payload: dict) -> dict:
    run_id = new_run_id("conv")
    run_dir = RUN_PATHS.ensure(RUN_PATHS.conversion_run(run_id))
    input_dir = RUN_PATHS.ensure(run_dir / "input")
    output_dir = RUN_PATHS.ensure(run_dir / "output")
    filename = _safe_filename(str(payload.get("filename", "upload.bin")))
    raw = base64.b64decode(payload.get("content_base64", ""), validate=True)
    if not raw:
        raise ValueError("empty upload")

    input_path = input_dir / filename
    input_path.write_bytes(raw)
    converter_id = str(payload.get("converter_id") or payload.get("converter") or "pymupdf4llm").lower()
    converter = get_converter(converter_id, CONFIG)
    conversion = converter.convert(input_path, output_dir, payload.get("options") or {})
    if conversion.status != "success":
        raise RuntimeError(conversion.stderr or f"{converter_id} conversion failed")

    markdown = conversion.markdown_path.read_text(encoding="utf-8", errors="replace")
    quality = QUALITY.evaluate(markdown).to_dict()
    pdf_name = Path(str(payload.get("pdf_name") or filename)).name
    benchmark = {"status": "skipped", "reason": "not a PDF or no golden dataset requested"}
    if input_path.suffix.lower() == ".pdf":
        benchmark = CepingAdapter(CONFIG).evaluate_markdown_file(conversion.markdown_path, pdf_name).to_dict()

    report = {
        "run_id": run_id,
        "run_type": "conversion_run",
        "status": "success",
        "created_at": utc_now_iso(),
        "filename": filename,
        "pdf_name": pdf_name,
        "conversion": conversion.to_dict(),
        "markdown_quality": quality,
        "converter_benchmark": benchmark,
        "markdown": markdown,
    }
    write_json(run_dir / "report.json", report)
    return report


def handle_md_quality(payload: dict) -> dict:
    run_id = new_run_id("mdq")
    markdown = str(payload.get("markdown", ""))
    result = QUALITY.evaluate(markdown).to_dict()
    report = {
        "run_id": run_id,
        "run_type": "md_quality_eval_run",
        "status": "success",
        "created_at": utc_now_iso(),
        "filename": payload.get("filename", "inline.md"),
        "markdown_quality": result,
    }
    write_json(RUN_PATHS.md_quality_run(run_id) / "report.json", report)
    return report


class Handler(BaseHTTPRequestHandler):
    server_version = "MDWebServerRefactored/0.1"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            _html_response(self, _web_index())
        elif path == "/api/converters":
            _json_response(self, {"converters": list_converters(CONFIG)})
        elif path == "/api/benchmark-summary":
            _json_response(self, {"rows": benchmark_summary()})
        elif path == "/health":
            _json_response(self, {"status": "ok"})
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if path == "/api/conversions":
                _json_response(self, handle_conversion(payload))
            elif path == "/api/md-quality-evaluations":
                _json_response(self, handle_md_quality(payload))
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except Exception as exc:  # noqa: BLE001
            _json_response(self, {"error": html.escape(str(exc))}, status=500)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run refactored MDWebServer.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8010)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    CONFIG.run_root.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving refactored MDWebServer on http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


