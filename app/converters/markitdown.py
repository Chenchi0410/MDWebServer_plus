from __future__ import annotations

import subprocess
import time
from pathlib import Path

from app.config import AppConfig
from app.converters.base import ConversionResult, EnvironmentStatus


class MarkItDownAdapter:
    id = "markitdown"
    name = "Microsoft MarkItDown"
    supported_extensions = {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".csv", ".json", ".xml", ".txt"}

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def check_environment(self) -> EnvironmentStatus:
        if not self.config.markitdown_python.exists():
            return EnvironmentStatus(False, f"Missing Python: {self.config.markitdown_python}")
        if not self.config.markitdown_cwd.exists():
            return EnvironmentStatus(False, f"Missing cwd: {self.config.markitdown_cwd}")
        version = self.get_version()
        return EnvironmentStatus(
            version != "unavailable",
            "ready" if version != "unavailable" else "MarkItDown import failed",
            {"python": str(self.config.markitdown_python), "version": version},
        )

    def get_version(self) -> str:
        if not self.config.markitdown_python.exists():
            return "unavailable"
        code = (
            "import importlib.metadata as m\n"
            "for name in ('markitdown', 'markitdown-mcp'):\n"
            "    try:\n"
            "        print(m.version(name))\n"
            "        raise SystemExit(0)\n"
            "    except m.PackageNotFoundError:\n"
            "        pass\n"
            "print('unknown')\n"
        )
        try:
            proc = subprocess.run(
                [str(self.config.markitdown_python), "-c", code],
                cwd=str(self.config.markitdown_cwd) if self.config.markitdown_cwd.exists() else None,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
            )
        except Exception:
            return "unavailable"
        if proc.returncode != 0:
            return "unavailable"
        return (proc.stdout.strip() or "unknown").splitlines()[-1]

    def convert(self, input_path: Path, output_dir: Path, options: dict | None = None) -> ConversionResult:
        if input_path.suffix.lower() not in self.supported_extensions:
            raise ValueError(f"MarkItDown does not support {input_path.suffix or 'this file type'}.")
        output_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = output_dir / "result.md"
        code = (
            "from pathlib import Path\n"
            "from markitdown import MarkItDown\n"
            "import sys\n"
            "src = Path(sys.argv[1])\n"
            "dst = Path(sys.argv[2])\n"
            "result = MarkItDown().convert(str(src))\n"
            "dst.parent.mkdir(parents=True, exist_ok=True)\n"
            "dst.write_text(result.text_content or '', encoding='utf-8')\n"
        )
        start = time.perf_counter()
        proc = subprocess.run(
            [str(self.config.markitdown_python), "-c", code, str(input_path), str(markdown_path)],
            cwd=str(self.config.markitdown_cwd),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.config.conversion_timeout_seconds,
        )
        status = "success" if proc.returncode == 0 and markdown_path.exists() else "failed"
        return ConversionResult(
            converter_id=self.id,
            status=status,
            input_path=input_path,
            markdown_path=markdown_path,
            duration_seconds=time.perf_counter() - start,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            output_bytes=markdown_path.stat().st_size if markdown_path.exists() else 0,
        )
