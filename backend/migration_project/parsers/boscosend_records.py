from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BoscoSendSection:
    """One active Bosco SEND section from a configuration.ini file."""

    nom_section: str
    remote_address: str | None
    remote_subdir: str | None
    localdir: str | None
    backup_dir: str | None
    file_search_mask: str | None
    cmdb_prestation: str | None
    cft_direct: str | None
    partner_code: str | None
    idf_code: str | None
