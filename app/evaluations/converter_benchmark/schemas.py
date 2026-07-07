from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConverterEvaluationResult:
    status: str
    pdf_name: str
    payload: dict

    def to_dict(self) -> dict:
        return {"status": self.status, "pdf_name": self.pdf_name, **self.payload}

