from __future__ import annotations

import hashlib
import re
from pathlib import Path


_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._ -]+")


def safe_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "upload.bin"
    cleaned = _SAFE_CHARS.sub("_", name).strip(" .")
    return cleaned or "upload.bin"


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_to(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")
