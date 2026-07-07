from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent


def _env_path(name: str, default: Path | str) -> Path:
    return Path(os.environ.get(name, str(default))).expanduser()


@dataclass(frozen=True)
class AppConfig:
    app_root: Path = APP_ROOT
    project_root: Path = PROJECT_ROOT
    run_root: Path = _env_path("MDWS_RUN_ROOT", APP_ROOT / "runs")
    dataset_dir: Path = _env_path("MDWS_DATASET_DIR", PROJECT_ROOT / "newbench")
    local_venv_python: Path = _env_path(
        "MDWS_LOCAL_VENV_PYTHON",
        PROJECT_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"),
    )
    ceping_evaluator: Path = _env_path("MDWS_CEPING_EVALUATOR", PROJECT_ROOT / "ceping" / "evaluate_file.py")
    markitdown_python: Path = _env_path(
        "MDWS_MARKITDOWN_PYTHON",
        Path(r"C:\Users\sangzs1\markitdown\.venv\Scripts\python.exe"),
    )
    markitdown_cwd: Path = _env_path("MDWS_MARKITDOWN_CWD", Path(r"C:\Users\sangzs1\markitdown"))
    conversion_timeout_seconds: int = int(os.environ.get("MDWS_CONVERSION_TIMEOUT", "180"))
    evaluation_timeout_seconds: int = int(os.environ.get("MDWS_EVALUATION_TIMEOUT", "240"))


def load_config() -> AppConfig:
    return AppConfig()

