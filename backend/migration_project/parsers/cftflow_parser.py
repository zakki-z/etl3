from __future__ import annotations

from pathlib import Path
from typing import Literal

from migration_project.parsers.common import extract_quoted, extract_value, truncate
from migration_project.parsers.records import FlowRecord


def parse_cftsend(file_path: Path) -> list[FlowRecord]:
    return _parse_flow_blocks(file_path, block_prefix="CFTSEND", direct="send")


def parse_cftrecv(file_path: Path) -> list[FlowRecord]:
    return _parse_flow_blocks(file_path, block_prefix="CFTRECV", direct="recv")


def _parse_flow_blocks(file_path: Path, block_prefix: str, direct: Literal["send", "recv"]) -> list[FlowRecord]:
    records: list[FlowRecord] = []
    current: dict[str, str | int | None] | None = None

    with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            stripped = raw_line.strip()
            if not stripped:
                continue

            # Business rule: if FRECFM is commented, keep it NULL.
            if current and stripped.startswith("/*") and "FRECFM" in stripped and "=" in stripped:
                current["frecfm"] = None
                continue

            if stripped.startswith(block_prefix):
                if current:
                    maybe = _to_flow_record(current, direct=direct)
                    if maybe:
                        records.append(maybe)

                current = {
                    "idf_code": extract_quoted(stripped),
                    "fcode": None,
                    "ftype": None,
                    "flrecl": None,
                    "frecfm": None,
                    "fname": None,
                    "xlate": 0,
                    "exec": None,
                    "exece": None,
                }
                continue

            if not current:
                continue

            if "MODE" in stripped and "REPLACE" in stripped:
                maybe = _to_flow_record(current, direct=direct)
                if maybe:
                    records.append(maybe)
                current = None
                continue

            if stripped.startswith("/*"):
                continue

            if "=" not in stripped:
                continue

            # Parse exact field name at the left of "=" to avoid
            # collisions like FRECFM vs NRECFM, FLRECL vs NLRECL, etc.
            left_side = stripped.split("=", 1)[0].strip()
            field = (left_side.split()[-1] if left_side else "").upper()

            if field == "FCODE":
                current["fcode"] = extract_value(stripped)
            elif field == "FTYPE":
                current["ftype"] = extract_value(stripped)
            elif field == "FLRECL":
                current["flrecl"] = extract_value(stripped)
            elif field == "FRECFM":
                current["frecfm"] = extract_value(stripped)
            elif field == "FNAME":
                current["fname"] = extract_value(stripped)
            elif field == "XLATE":
                current["xlate"] = 1 if extract_quoted(stripped) else 0
            elif field == "EXECE":
                # Must be before EXEC: "EXECE" contains "EXEC" as substring when matching loosely.
                current["exece"] = truncate(extract_value(stripped), 1000)
            elif field == "EXEC":
                current["exec"] = truncate(extract_value(stripped), 1000)

    if current:
        maybe = _to_flow_record(current, direct=direct)
        if maybe:
            records.append(maybe)

    return records


def _to_flow_record(data: dict[str, str | int | None], direct: Literal["send", "recv"]) -> FlowRecord | None:
    idf_code = str(data.get("idf_code") or "").strip()
    if not idf_code:
        return None

    return FlowRecord(
        idf_code=idf_code,
        direct=direct,
        fcode=truncate(data.get("fcode"), 100),  # type: ignore[arg-type]
        ftype=truncate(data.get("ftype"), 100),  # type: ignore[arg-type]
        flrecl=truncate(data.get("flrecl"), 100),  # type: ignore[arg-type]
        frecfm=truncate(data.get("frecfm"), 100),  # type: ignore[arg-type]
        fname=truncate(data.get("fname"), 100),  # type: ignore[arg-type]
        xlate=int(data.get("xlate") or 0),
        exec=data.get("exec"),  # type: ignore[arg-type]
        exece=data.get("exece"),  # type: ignore[arg-type]
    )
