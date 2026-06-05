from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


VALUE_RE = re.compile(r"'([^']*)'")


def extract_quoted(line: str) -> str | None:
    match = VALUE_RE.search(line)
    return match.group(1).strip() if match else None


def extract_value(line: str) -> str | None:
    quoted = extract_quoted(line)
    if quoted is not None:
        return quoted

    if "=" not in line:
        return None

    raw = line.split("=", 1)[1].strip()
    if not raw:
        return None

    # Strip trailing separators commonly found in conf lines.
    raw = raw.rstrip(",;").strip()
    return raw or None


def truncate(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if len(value) <= max_len:
        return value
    return value[:max_len]


def iter_clean_lines(file_path: Path) -> Iterable[str]:
    with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("/*"):
                continue
            yield stripped
