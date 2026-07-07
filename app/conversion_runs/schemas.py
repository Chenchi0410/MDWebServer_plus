from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ConverterInfo:
    id: str
    name: str
    version: str


@dataclass(frozen=True)
class ConversionInput:
    filename: str
    input_type: str
    sha256: str
    bytes: int


@dataclass(frozen=True)
class ConversionOutput:
    markdown_path: str
    markdown_sha256: str
    bytes: int


@dataclass(frozen=True)
class ConversionRuntime:
    duration_seconds: float
    returncode: int | None
    timeout_seconds: int


@dataclass(frozen=True)
class ConversionArtifacts:
    input_path: str
    output_dir: str
    stdout_path: str
    stderr_path: str
    conversion_result_path: str


@dataclass(frozen=True)
class ConversionRunResult:
    run_id: str
    run_type: str
    status: str
    created_at: str
    finished_at: str
    converter: ConverterInfo
    input: ConversionInput
    output: ConversionOutput
    runtime: ConversionRuntime
    logs: dict[str, str]
    artifacts: ConversionArtifacts
    markdown: str
    error: str | None = None

    def to_dict(self, include_markdown: bool = False) -> dict:
        payload = asdict(self)
        if not include_markdown:
            payload.pop("markdown", None)
        if self.error is None:
            payload.pop("error", None)
        return payload

    def to_api_response(self) -> dict:
        payload = self.to_dict(include_markdown=True)
        payload["conversion_result_path"] = self.artifacts.conversion_result_path
        return payload
