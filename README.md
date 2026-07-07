# MDWebServer Refactored MVP

This directory contains the refactored architecture baseline for MdWebServer.
It is intentionally kept separate from the current demo implementation so the
existing MVP can keep running while the new structure is migrated module by
module.

## Goals

The refactored version separates three capabilities:

1. Markdown conversion service
2. Converter benchmark evaluation with golden datasets
3. Markdown file quality evaluation without golden datasets

## Run

From `C:\Users\sangzs1\MdWebServer`:

```powershell
& '.\.venv\Scripts\python.exe' .\MDWebServer\app\main.py --host 127.0.0.1 --port 8010
```

Then open:

```text
http://127.0.0.1:8010/
```

## Structure

```text
MDWebServer/
  app/
    main.py
    config.py
    api/
    converters/
    evaluations/
      converter_benchmark/
      md_quality/
    schemas/
    storage/
    web/
  runs/
  config.example.toml
```

## Current Integration

- `markitdown` and `pymupdf4llm` are implemented as converter adapters.
- Markdown quality evaluation is independent of golden datasets.
- Converter benchmark evaluation calls the existing `ceping` system through a
  dedicated adapter.
- Existing root-level assets such as `newbench`, `ceping`, `.venv`, and
  `benchmark_runs` are reused through configuration defaults.

