from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class EnvironmentStatus:
    available: bool
    message: str = ""
    details: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ConversionResult:
    converter_id: str
    status: str
    input_path: Path
    markdown_path: Path
    duration_seconds: float
    returncode: int | None
    stdout: str = ""
    stderr: str = ""
    output_bytes: int = 0

    def to_dict(self) -> dict:
        return {
            "converter_id": self.converter_id,
            "status": self.status,
            "input_path": str(self.input_path),
            "markdown_path": str(self.markdown_path),
            "duration_seconds": round(self.duration_seconds, 3),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "output_bytes": self.output_bytes,
        }


class ConverterAdapter(Protocol):
    id: str
    name: str
    supported_extensions: set[str]

    def check_environment(self) -> EnvironmentStatus:
        ...

    def get_version(self) -> str:
        ...

    def convert(self, input_path: Path, output_dir: Path, options: dict | None = None) -> ConversionResult:
        ...
