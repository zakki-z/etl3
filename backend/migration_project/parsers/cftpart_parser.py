from __future__ import annotations

from pathlib import Path

from migration_project.parsers.common import extract_quoted, iter_clean_lines
from migration_project.parsers.records import PartnerRecord


def parse_cftpart(file_path: Path) -> list[PartnerRecord]:
    records: list[PartnerRecord] = []
    current: dict[str, str | int | None] | None = None

    for stripped in iter_clean_lines(file_path):
        if stripped.startswith("CFTPART"):
            if current:
                records.append(_to_partner_record(current))
            current = {
                "conf_id": extract_quoted(stripped),
                "nspart": None,
                "nrpart": None,
                "ipart": None,
                "sap": None,
                "nspassw": None,
                "nrpassw": None,
                "ssl": 0,
            }
            continue

        if not current:
            continue

        if "MODE" in stripped and "REPLACE" in stripped:
            records.append(_to_partner_record(current))
            current = None
            continue

        left_side = stripped.split("=", 1)[0].strip() if "=" in stripped else ""
        field = (left_side.split()[-1] if left_side else "").upper()

        if field == "NSPART":
            current["nspart"] = extract_quoted(stripped)
        elif field == "NRPART":
            current["nrpart"] = extract_quoted(stripped)
        elif field == "IPART":
            current["ipart"] = extract_quoted(stripped)
        elif "SAP" in stripped and "=" in stripped:
            current["sap"] = extract_quoted(stripped)
        elif "NSPASSW" in stripped and "=" in stripped:
            current["nspassw"] = extract_quoted(stripped)
        elif "NRPASSW" in stripped and "=" in stripped:
            current["nrpassw"] = extract_quoted(stripped)
        elif "SSL" in stripped and "=" in stripped:
            current["ssl"] = 1 if extract_quoted(stripped) else 0

    if current:
        records.append(_to_partner_record(current))

    return [r for r in records if r.nspart and r.nrpart and r.conf_id]


def _to_partner_record(data: dict[str, str | int | None]) -> PartnerRecord:
    return PartnerRecord(
        conf_id=str(data.get("conf_id") or ""),
        nspart=data.get("nspart"),  # type: ignore[arg-type]
        nrpart=data.get("nrpart"),  # type: ignore[arg-type]
        ipart=data.get("ipart"),  # type: ignore[arg-type]
        sap=data.get("sap"),  # type: ignore[arg-type]
        nspassw=data.get("nspassw"),  # type: ignore[arg-type]
        nrpassw=data.get("nrpassw"),  # type: ignore[arg-type]
        ssl=int(data.get("ssl") or 0),
    )
