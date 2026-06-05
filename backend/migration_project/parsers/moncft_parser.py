from __future__ import annotations

import configparser
import re
from pathlib import Path

from migration_project.parsers.moncft_records import MonCftRepertoire


_REPERTOIRE_SECTION_RE = re.compile(r"^repertoire\s*:?\s*\d+$", re.IGNORECASE)


def is_moncft_copy_file(file_path: Path) -> bool:
    """Skip backups like 'C2I_MonCftCAARCT - Copy.ini' or '... - Copy (2).ini'."""
    return "copy" in file_path.name.lower()


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def parse_moncft_file(file_path: Path) -> list[MonCftRepertoire]:
    """Parse a C2I_MonCft<XXX>.ini file and return one record per [Repertoire : N]."""
    parser = configparser.ConfigParser(
        interpolation=None,
        strict=False,
        allow_no_value=True,
    )
    parser.optionxform = str  # preserve case in keys

    try:
        parser.read(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        parser.read(file_path, encoding="latin-1")

    records: list[MonCftRepertoire] = []
    for section_name in parser.sections():
        if not _REPERTOIRE_SECTION_RE.match(section_name.strip()):
            continue

        section = parser[section_name]
        idf_code = _clean(section.get("IDF"))
        partner_code = _clean(section.get("PART"))

        # IDF and PART are the only mandatory fields to map to a transfer.
        if not idf_code or not partner_code:
            continue

        records.append(
            MonCftRepertoire(
                idf_code=idf_code,
                partner_code=partner_code,
                fname=_clean(section.get("Repertoire Fname")),
                filtre=_clean(section.get("Filtre (* par defaut)")),
                parm=_clean(section.get("PARM")),
                nfname=_clean(section.get("NFNAME")),
                sappl=_clean(section.get("SAPPL")),
                rappl=_clean(section.get("RAPPL")),
                suser=_clean(section.get("SUSER")),
            )
        )

    return records
