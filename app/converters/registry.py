from __future__ import annotations

from app.config import AppConfig, load_config
from app.converters.base import ConverterAdapter
from app.converters.markitdown import MarkItDownAdapter
from app.converters.pymupdf4llm import PyMuPDF4LLMAdapter


def build_registry(config: AppConfig | None = None) -> dict[str, ConverterAdapter]:
    cfg = config or load_config()
    adapters = [
        MarkItDownAdapter(cfg),
        PyMuPDF4LLMAdapter(cfg),
    ]
    return {adapter.id: adapter for adapter in adapters}


def get_converter(converter_id: str, config: AppConfig | None = None) -> ConverterAdapter:
    registry = build_registry(config)
    try:
        return registry[converter_id]
    except KeyError as exc:
        raise KeyError(f"Unknown converter: {converter_id}") from exc


def list_converters(config: AppConfig | None = None) -> list[dict]:
    rows = []
    for adapter in build_registry(config).values():
        status = adapter.check_environment()
        rows.append(
            {
                "id": adapter.id,
                "name": adapter.name,
                "supported_extensions": sorted(adapter.supported_extensions),
                "available": status.available,
                "message": status.message,
            }
        )
    return rows

