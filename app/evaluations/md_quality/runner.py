from __future__ import annotations

from app.config import AppConfig, load_config
from app.evaluations.md_quality.pymarkdown_adapter import evaluate_pymarkdown
from app.evaluations.md_quality.rules import evaluate_encoding, evaluate_readability, evaluate_structure, evaluate_tables
from app.evaluations.md_quality.schemas import MarkdownQualityResult


class MarkdownQualityEvaluator:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()

    def evaluate(self, markdown: str) -> MarkdownQualityResult:
        dimensions = [
            evaluate_pymarkdown(markdown, self.config),
            evaluate_encoding(markdown),
            evaluate_structure(markdown),
            evaluate_tables(markdown),
            evaluate_readability(markdown),
        ]
        issue_count = sum(len(d.issues) for d in dimensions)
        overall = sum(d.score for d in dimensions) / len(dimensions) if dimensions else 0.0
        summary = {
            "char_count": len(markdown),
            "line_count": markdown.count("\n") + (1 if markdown else 0),
        }
        return MarkdownQualityResult(overall, dimensions, issue_count, summary)

