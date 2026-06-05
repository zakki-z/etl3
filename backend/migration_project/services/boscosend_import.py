from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.config import get_settings
from migration_project.parsers.boscosend_parser import parse_boscosend_file
from migration_project.parsers.boscosend_records import BoscoSendSection
from migration_project.repositories.boscosend_config_repository import (
    BoscoSendConfigRepository,
)
from migration_project.utils.file_selector import get_server_boscosend_files


@dataclass
class BoscoSendImportReport:
    servers_scanned: int = 0
    files_seen: int = 0
    sections_parsed: int = 0
    inserted_with_transfer: int = 0
    inserted_without_transfer: int = 0
    missing_cft_mapping: int = 0
    unknown_idf: int = 0
    unknown_partner: int = 0
    missing_transfer: int = 0
    missing_servers: list[str] = field(default_factory=list)


class BoscoSendImportService:
    """Parse Bosco SEND configuration.ini files under <data_dir>/<server>/boscosend/."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.repository = BoscoSendConfigRepository()

    def run(self, session: Session) -> BoscoSendImportReport:
        report = BoscoSendImportReport()

        valid_server_ids = self._load_valid_server_ids(session)
        flow_index = self._load_flow_index(session)
        partner_ids = self._load_partner_ids(session)
        transfer_index = self._load_transfer_index(session)

        # Wipe & rebuild: each run mirrors the current Bosco SEND config files.
        self.repository.wipe(session)
        session.flush()

        rows_to_insert: list[dict] = []

        for server_id, config_file in get_server_boscosend_files(self.settings.data_dir):
            report.servers_scanned += 1

            if server_id not in valid_server_ids:
                report.missing_servers.append(server_id)
                continue

            report.files_seen += 1
            records = parse_boscosend_file(config_file)
            report.sections_parsed += len(records)

            for record in records:
                rows_to_insert.append(
                    self._record_to_row(
                        record=record,
                        server_id=server_id,
                        flow_index=flow_index,
                        partner_ids=partner_ids,
                        transfer_index=transfer_index,
                        report=report,
                    )
                )

        self.repository.insert_many(session, rows_to_insert)

        return report

    # -- Internals ------------------------------------------------------------

    def _record_to_row(
        self,
        *,
        record: BoscoSendSection,
        server_id: str,
        flow_index: dict[tuple[str, str], int],
        partner_ids: set[str],
        transfer_index: dict[tuple[str, int, str], int],
        report: BoscoSendImportReport,
    ) -> dict:
        transfer_id = self._resolve_transfer_id(
            record=record,
            server_id=server_id,
            flow_index=flow_index,
            partner_ids=partner_ids,
            transfer_index=transfer_index,
            report=report,
        )

        if transfer_id is None:
            report.inserted_without_transfer += 1
        else:
            report.inserted_with_transfer += 1

        return {
            "remote_address": record.remote_address,
            "remote_subdir": record.remote_subdir,
            "transfer_id": transfer_id,
            "localdir": record.localdir,
            "backup_dir": record.backup_dir,
            "file_search_mask": record.file_search_mask,
            "nom_section": record.nom_section,
            "cmdb_prestation": record.cmdb_prestation,
        }

    def _resolve_transfer_id(
        self,
        *,
        record: BoscoSendSection,
        server_id: str,
        flow_index: dict[tuple[str, str], int],
        partner_ids: set[str],
        transfer_index: dict[tuple[str, int, str], int],
        report: BoscoSendImportReport,
    ) -> int | None:
        if not record.cft_direct or not record.partner_code or not record.idf_code:
            report.missing_cft_mapping += 1
            return None

        if record.partner_code not in partner_ids:
            report.unknown_partner += 1
            return None

        idf_id = flow_index.get((record.idf_code.lower(), record.cft_direct))
        if idf_id is None:
            report.unknown_idf += 1
            return None

        transfer_id = transfer_index.get((server_id, idf_id, record.partner_code))
        if transfer_id is None:
            report.missing_transfer += 1
            return None

        return transfer_id

    # -- Lookups --------------------------------------------------------------

    def _load_valid_server_ids(self, session: Session) -> set[str]:
        rows = session.execute(text("SELECT id FROM server")).mappings().all()
        return {str(r["id"]) for r in rows}

    def _load_flow_index(self, session: Session) -> dict[tuple[str, str], int]:
        """(idf_code lowercased, direct) -> cft_flow.id."""
        rows = session.execute(text("SELECT id, idf_code, direct FROM cft_flow")).mappings().all()
        return {
            (str(r["idf_code"]).lower(), str(r["direct"]).lower()): int(r["id"])
            for r in rows
        }

    def _load_partner_ids(self, session: Session) -> set[str]:
        rows = session.execute(text("SELECT id FROM cft_partner")).mappings().all()
        return {str(r["id"]) for r in rows}

    def _load_transfer_index(self, session: Session) -> dict[tuple[str, int, str], int]:
        """(server_id, idf_id, partner_id) -> transfer.id."""
        rows = (
            session.execute(
                text(
                    """
                    SELECT id, server_id, idf_id, partner_id
                    FROM transfer
                    WHERE server_id IS NOT NULL
                      AND idf_id IS NOT NULL
                      AND partner_id IS NOT NULL
                    """
                )
            )
            .mappings()
            .all()
        )
        out: dict[tuple[str, int, str], int] = {}
        for r in rows:
            key = (str(r["server_id"]), int(r["idf_id"]), str(r["partner_id"]))
            if key not in out:
                out[key] = int(r["id"])
        return out
