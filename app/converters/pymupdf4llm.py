from __future__ import annotations

import subprocess
import time
from pathlib import Path

from app.config import AppConfig
from app.converters.base import ConversionResult, EnvironmentStatus


class PyMuPDF4LLMAdapter:
    id = "pymupdf4llm"
    name = "PyMuPDF4LLM"
    supported_extensions = {".pdf"}

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def check_environment(self) -> EnvironmentStatus:
        if not self.config.local_venv_python.exists():
            return EnvironmentStatus(False, f"Missing Python: {self.config.local_venv_python}")
        return EnvironmentStatus(True, "ready", {"python": str(self.config.local_venv_python)})

    def convert(self, input_path: Path, output_dir: Path, options: dict | None = None) -> ConversionResult:
        if input_path.suffix.lower() not in self.supported_extensions:
            raise ValueError("PyMuPDF4LLM only supports PDF files.")
        output_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = output_dir / f"{input_path.stem}.md"
        code = (
            "from pathlib import Path\n"
            "import sys\n"
            "import pymupdf4llm\n"
            "src = Path(sys.argv[1])\n"
            "dst = Path(sys.argv[2])\n"
            "markdown = pymupdf4llm.to_markdown(str(src))\n"
            "if isinstance(markdown, list):\n"
            "    markdown = '\\n\\n'.join(str(item) for item in markdown)\n"
            "dst.parent.mkdir(parents=True, exist_ok=True)\n"
            "dst.write_text(markdown or '', encoding='utf-8')\n"
        )
        start = time.perf_counter()
        proc = subprocess.run(
            [str(self.config.local_venv_python), "-c", code, str(input_path), str(markdown_path)],
            cwd=str(self.config.project_root),
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

