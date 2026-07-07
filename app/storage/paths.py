from __future__ import annotations

from pathlib import Path

from app.config import AppConfig, load_config


class RunPaths:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()

    def conversion_run(self, run_id: str) -> Path:
        return self.config.run_root / "conversions" / run_id

    def md_quality_run(self, run_id: str) -> Path:
        return self.config.run_root / "md_quality" / run_id

    def ensure(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path

