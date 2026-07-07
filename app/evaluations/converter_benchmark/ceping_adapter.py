from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.config import AppConfig, load_config
from app.evaluations.converter_benchmark.schemas import ConverterEvaluationResult


class CepingAdapter:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()

    def evaluate_markdown_file(self, markdown_path: Path, pdf_name: str) -> ConverterEvaluationResult:
        if not pdf_name:
            return ConverterEvaluationResult("skipped", pdf_name, {"reason": "missing pdf_name"})
        if not self.config.ceping_evaluator.exists():
            return ConverterEvaluationResult(
                "skipped",
                pdf_name,
                {"reason": f"missing ceping evaluator: {self.config.ceping_evaluator}"},
            )
        proc = subprocess.run(
            [
                str(self.config.local_venv_python),
                str(self.config.ceping_evaluator),
                "--markdown-path",
                str(markdown_path),
                "--pdf-name",
                pdf_name,
                "--dataset-dir",
                str(self.config.dataset_dir),
            ],
            cwd=str(self.config.project_root),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.config.evaluation_timeout_seconds,
        )
        if proc.returncode != 0:
            return ConverterEvaluationResult("error", pdf_name, {"reason": proc.stderr.strip()})
        try:
            payload = json.loads(proc.stdout.strip() or "{}")
        except json.JSONDecodeError:
            return ConverterEvaluationResult("error", pdf_name, {"reason": "ceping returned non-json"})
        return ConverterEvaluationResult(str(payload.get("status", "success")), pdf_name, payload)

