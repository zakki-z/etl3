from __future__ import annotations

import configparser
import re
from pathlib import Path

from migration_project.parsers.boscosend_records import BoscoSendSection


_CFT_LOCALDIR_RE = re.compile(
    r"(?:^|[/\\])CFT[/\\](?P<direct>recv|send)[/\\](?P<partner>[^/\\]+)[/\\](?P<idf>[^/\\]+)",
    re.IGNORECASE,
)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _contains_copilote(*values: str | None) -> bool:
    return any(value is not None and "copilote" in value.lower() for value in values)


def _extract_cft_mapping(localdir: str | None) -> tuple[str | None, str | None, str | None]:
    if localdir is None:
        return None, None, None

    match = _CFT_LOCALDIR_RE.search(localdir)
    if match is None:
        return None, None, None

    return (
        match.group("direct").lower(),
        match.group("partner"),
        match.group("idf"),
    )


def parse_boscosend_file(file_path: Path) -> list[BoscoSendSection]:
    """Parse active Bosco SEND sections from a boscosend/configuration.ini file."""
    parser = configparser.ConfigParser(
        interpolation=None,
        strict=False,
        allow_no_value=True,
    )
    parser.optionxform = str  # preserve key case, especially "Cmdb-Prestation"

    try:
        parser.read(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        parser.read(file_path, encoding="latin-1")

    records: list[BoscoSendSection] = []
    for section_name in parser.sections():
        section = parser[section_name]
        localdir = _clean(section.get("localDir"))
        remote_address = _clean(section.get("remoteAddress"))
        remote_subdir = _clean(section.get("remoteSubDir"))
        backup_dir = _clean(section.get("backupDir"))

        # Keep only real Bosco SEND entries. Scheduler jobs do not have both fields.
        if not localdir or not remote_address:
            continue

        if _contains_copilote(section_name, localdir, remote_subdir, backup_dir):
            continue

        cft_direct, partner_code, idf_code = _extract_cft_mapping(localdir)

        records.append(
            BoscoSendSection(
                nom_section=section_name.strip(),
                remote_address=remote_address,
                remote_subdir=remote_subdir,
                localdir=localdir,
                backup_dir=backup_dir,
                file_search_mask=_clean(section.get("fileSearchMask")),
                cmdb_prestation=_clean(section.get("Cmdb-Prestation")),
                cft_direct=cft_direct,
                partner_code=partner_code,
                idf_code=idf_code,
            )
        )

    return records
