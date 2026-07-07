from __future__ import annotations

import sys
from pathlib import Path

from app.config import AppConfig
from app.evaluations.md_quality.schemas import DimensionScore, QualityIssue


def evaluate_pymarkdown(markdown: str, config: AppConfig) -> DimensionScore:
    ceping_dir = config.project_root / "ceping"
    parsebench_src = ceping_dir / "ParseBench-main" / "src"
    sys.path.insert(0, str(ceping_dir))
    sys.path.insert(0, str(parsebench_src))
    try:
        from eval.layers.l1_format import L1FormatEvaluator
    except Exception as exc:  # noqa: BLE001
        return DimensionScore(
            "syntax",
            0.0,
            [QualityIssue("syntax.unavailable", "medium", f"PyMarkdown lint 不可用：{exc}")],
        )

    result = L1FormatEvaluator().evaluate_detailed(markdown)
    issues = [
        QualityIssue(
            rule_id=str(item.get("rule_id", "syntax")),
            severity="low",
            message=str(item.get("description", "Markdown lint issue")),
            line=int(item["line"]) if item.get("line") is not None else None,
            column=int(item["column"]) if item.get("column") is not None else None,
        )
        for item in result.violations[:50]
    ]
    return DimensionScore("syntax", result.score, issues)

