from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QualityIssue:
    rule_id: str
    severity: str
    message: str
    line: int | None = None
    column: int | None = None


@dataclass(frozen=True)
class DimensionScore:
    dimension: str
    score: float
    issues: list[QualityIssue] = field(default_factory=list)


@dataclass(frozen=True)
class MarkdownQualityResult:
    overall_score: float
    dimensions: list[DimensionScore]
    issue_count: int
    summary: dict

    def to_dict(self) -> dict:
        return {
            "overall_score": round(self.overall_score, 2),
            "issue_count": self.issue_count,
            "summary": self.summary,
            "dimensions": [
                {
                    "dimension": d.dimension,
                    "score": round(d.score, 2),
                    "issues": [issue.__dict__ for issue in d.issues],
                }
                for d in self.dimensions
            ],
        }

