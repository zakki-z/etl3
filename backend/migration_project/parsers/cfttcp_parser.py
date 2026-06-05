from __future__ import annotations

from pathlib import Path

from migration_project.parsers.common import extract_quoted, iter_clean_lines
from migration_project.parsers.records import TcpRecord


def parse_cfttcp(file_path: Path) -> list[TcpRecord]:
    records: list[TcpRecord] = []
    current: dict[str, str | None] | None = None

    for stripped in iter_clean_lines(file_path):
        if stripped.startswith("CFTTCP"):
            if current:
                records.append(_to_tcp_record(current))
            current = {"conf_id": extract_quoted(stripped), "cnxout": None, "host": None}
            continue

        if not current:
            continue

        if "MODE" in stripped and "REPLACE" in stripped:
            records.append(_to_tcp_record(current))
            current = None
            continue

        if "CNXOUT" in stripped and "=" in stripped:
            current["cnxout"] = extract_quoted(stripped)
        elif "HOST" in stripped and "=" in stripped:
            current["host"] = extract_quoted(stripped)

    if current:
        records.append(_to_tcp_record(current))

    return [r for r in records if r.conf_id]


def _to_tcp_record(data: dict[str, str | None]) -> TcpRecord:
    return TcpRecord(
        conf_id=str(data.get("conf_id") or ""),
        cnxout=data.get("cnxout"),
        host=data.get("host"),
    )
