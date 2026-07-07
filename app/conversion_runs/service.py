from __future__ import annotations

import json
from pathlib import Path

from app.config import AppConfig, load_config
from app.conversion_runs.artifacts import relative_to, safe_filename, sha256_bytes, sha256_file, write_text
from app.conversion_runs.schemas import (
    ConversionArtifacts,
    ConversionInput,
    ConversionOutput,
    ConversionRunResult,
    ConversionRuntime,
    ConverterInfo,
)
from app.converters.registry import get_converter
from app.schemas.common import new_run_id, utc_now_iso
from app.storage.paths import RunPaths


class ConversionService:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()
        self.paths = RunPaths(self.config)

    def create_conversion_run(
        self,
        filename: str,
        content: bytes,
        converter_id: str,
        options: dict | None = None,
    ) -> ConversionRunResult:
        if not content:
            raise ValueError("empty upload")

        run_id = new_run_id("conv")
        run_dir = self.paths.ensure(self.paths.conversion_run(run_id))
        input_dir = self.paths.ensure(run_dir / "input")
        output_dir = self.paths.ensure(run_dir / "output")
        logs_dir = self.paths.ensure(run_dir / "logs")

        created_at = utc_now_iso()
        clean_name = safe_filename(filename)
        input_path = input_dir / clean_name
        input_path.write_bytes(content)

        converter = get_converter(converter_id.lower(), self.config)
        if input_path.suffix.lower() not in converter.supported_extensions:
            raise ValueError(f"{converter.name} does not support {input_path.suffix or 'this file type'}.")

        env = converter.check_environment()
        if not env.available:
            raise RuntimeError(env.message or f"{converter.name} is unavailable")

        conversion = converter.convert(input_path, output_dir, options or {})
        stdout_path = logs_dir / "stdout.txt"
        stderr_path = logs_dir / "stderr.txt"
        write_text(stdout_path, conversion.stdout)
        write_text(stderr_path, conversion.stderr)

        markdown = ""
        markdown_sha256 = ""
        markdown_bytes = 0
        if conversion.markdown_path.exists():
            markdown = conversion.markdown_path.read_text(encoding="utf-8", errors="replace")
            markdown_sha256 = sha256_file(conversion.markdown_path)
            markdown_bytes = conversion.markdown_path.stat().st_size

        status = "success" if conversion.status == "success" else "failed"
        error = None if status == "success" else (conversion.stderr.strip() or f"{converter.name} conversion failed")
        finished_at = utc_now_iso()
        result_path = run_dir / "conversion_result.json"

        result = ConversionRunResult(
            run_id=run_id,
            run_type="conversion_run",
            status=status,
            created_at=created_at,
            finished_at=finished_at,
            converter=ConverterInfo(id=converter.id, name=converter.name, version=converter.get_version()),
            input=ConversionInput(
                filename=clean_name,
                input_type=input_path.suffix.lower().lstrip(".") or "unknown",
                sha256=sha256_bytes(content),
                bytes=len(content),
            ),
            output=ConversionOutput(
                markdown_path=relative_to(conversion.markdown_path, run_dir),
                markdown_sha256=markdown_sha256,
                bytes=markdown_bytes,
            ),
            runtime=ConversionRuntime(
                duration_seconds=round(conversion.duration_seconds, 3),
                returncode=conversion.returncode,
                timeout_seconds=self.config.conversion_timeout_seconds,
            ),
            logs={
                "stdout_path": relative_to(stdout_path, run_dir),
                "stderr_path": relative_to(stderr_path, run_dir),
            },
            artifacts=ConversionArtifacts(
                input_path=relative_to(input_path, run_dir),
                output_dir=relative_to(output_dir, run_dir),
                stdout_path=relative_to(stdout_path, run_dir),
                stderr_path=relative_to(stderr_path, run_dir),
                conversion_result_path=relative_to(result_path, self.config.app_root),
            ),
            markdown=markdown,
            error=error,
        )
        result_path.write_text(json.dumps(result.to_dict(include_markdown=False), ensure_ascii=False, indent=2), encoding="utf-8")
        return result

