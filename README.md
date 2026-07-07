# MDWebServer Plus - Converter Service MVP

当前阶段只聚焦一件事：提供稳定、干净、可扩展的多 Markdown 转换器服务。

本阶段负责：

```text
输入文件 + 选择转换器 -> 输出 Markdown + 转换元数据 + 日志
```

本阶段暂不负责：

```text
ceping 评测
黄金数据集评测
Markdown 质量评分
转换器效果打分
复杂 benchmark 展示
```

## Run

From `C:\Users\sangzs1\MdWebServer\MDWebServer`:

```powershell
& '..\.venv\Scripts\python.exe' .\app\main.py --host 127.0.0.1 --port 8010
```

Then open:

```text
http://127.0.0.1:8010/
```

## APIs

### GET /api/converters

Returns all converter adapters and their environment status.

Optional filter:

```text
/api/converters?extension=pdf
```

### POST /api/conversions

Input:

```json
{
  "filename": "example.pdf",
  "content_base64": "...",
  "converter_id": "pymupdf4llm",
  "options": {}
}
```

Output includes `run_id`, converter metadata, artifact paths, runtime metadata, and a Markdown preview.

## Standard Conversion Artifacts

Every conversion creates:

```text
runs/conversions/{run_id}/
  input/
    original_file
  output/
    result.md
  logs/
    stdout.txt
    stderr.txt
  conversion_result.json
```

`conversion_result.json` stores metadata and paths only. The Markdown body is stored in `output/result.md` and returned by the API for preview.

## Current Converters

- Microsoft MarkItDown
- PyMuPDF4LLM

## Structure

```text
app/
  main.py
  config.py
  conversion_runs/
    artifacts.py
    schemas.py
    service.py
  converters/
    base.py
    registry.py
    markitdown.py
    pymupdf4llm.py
  storage/
    paths.py
    run_store.py
  schemas/
    common.py
  web/
    index.html
```

The `evaluations/` package may remain in the repository for later integration, but it is not imported or used by the current conversion service flow.
