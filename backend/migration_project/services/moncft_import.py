from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.config import get_settings
from migration_project.parsers.moncft_parser import (
    is_moncft_copy_file,
    parse_moncft_file,
)
from migration_project.parsers.moncft_records import MonCftRepertoire
from migration_project.repositories.moncft_config_repository import (
    MonCftConfigRepository,
)
from migration_project.utils.file_selector import get_server_moncft_dirs


@dataclass
class MonCftImportReport:
    servers_scanned: int = 0
    files_seen: int = 0
    files_skipped_copy: int = 0
    sections_parsed: int = 0
    inserted_with_transfer: int = 0
    inserted_without_transfer: int = 0
    skipped_unknown_idf: int = 0
    skipped_unknown_partner: int = 0
    missing_servers: list[str] = field(default_factory=list)


class MonCftImportService:
    """Parse C2I_MonCft<XXX>.ini files under <data_dir>/<server>/moncft/.

    Each '[Repertoire : N]' section becomes one row in moncft_config, with
    transfer_id resolved through cft_flow (idf_code + direct='send') and
    cft_partner (PART code) then transfer (server_id + idf_id + partner_id).
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.repository = MonCftConfigRepository()

    def run(self, session: Session) -> MonCftImportReport:
        report = MonCftImportReport()

        valid_server_ids = self._load_valid_server_ids(session)
        send_flow_index = self._load_send_flow_index(session)
        partner_ids = self._load_partner_ids(session)
        transfer_index = self._load_transfer_index(session)

        # Wipe & rebuild: idempotent snapshot at every run.
        self.repository.wipe(session)
        session.flush()

        rows_to_insert: list[dict] = []

        for server_id, moncft_dir in get_server_moncft_dirs(self.settings.data_dir):
            report.servers_scanned += 1

            if server_id not in valid_server_ids:
                report.missing_servers.append(server_id)
                continue

            for ini_file in sorted(moncft_dir.iterdir()):
                if not ini_file.is_file():
                    continue
                if ini_file.suffix.lower() != ".ini":
                    continue
                if is_moncft_copy_file(ini_file):
                    report.files_skipped_copy += 1
                    continue

                report.files_seen += 1
                records = parse_moncft_file(ini_file)
                report.sections_parsed += len(records)

                for record in records:
                    row = self._record_to_row(
                        record=record,
                        server_id=server_id,
                        send_flow_index=send_flow_index,
                        partner_ids=partner_ids,
                        transfer_index=transfer_index,
                        report=report,
                    )
                    if row is not None:
                        rows_to_insert.append(row)

        self.repository.insert_many(session, rows_to_insert)

        return report

    # -- Internals ------------------------------------------------------------

    def _record_to_row(
        self,
        *,
        record: MonCftRepertoire,
        server_id: str,
        send_flow_index: dict[str, int],
        partner_ids: set[str],
        transfer_index: dict[tuple[str, int, str], int],
        report: MonCftImportReport,
    ) -> dict | None:
        # Case A: IDF must exist as a 'send' flow.
        idf_id = send_flow_index.get(record.idf_code.lower())
        if idf_id is None:
            report.skipped_unknown_idf += 1
            return None

        # Case B: PART must exist in cft_partner.
        if record.partner_code not in partner_ids:
            report.skipped_unknown_partner += 1
            return None

        # Case C: transfer may or may not exist; we insert in both cases.
        transfer_id = transfer_index.get((server_id, idf_id, record.partner_code))
        if transfer_id is None:
            report.inserted_without_transfer += 1
        else:
            report.inserted_with_transfer += 1

        return {
            "transfer_id": transfer_id,
            "fname": record.fname,
            "filtre": record.filtre,
            "parm": record.parm,
            "nfname": record.nfname,
            "sappl": record.sappl,
            "rappl": record.rappl,
            "suser": record.suser,
        }

    # -- Lookups --------------------------------------------------------------

    def _load_valid_server_ids(self, session: Session) -> set[str]:
        rows = session.execute(text("SELECT id FROM server")).mappings().all()
        return {str(r["id"]) for r in rows}

    def _load_send_flow_index(self, session: Session) -> dict[str, int]:
        """idf_code (lowercased) -> cft_flow.id for direct='send'."""
        rows = (
            session.execute(
                text("SELECT id, idf_code FROM cft_flow WHERE direct = 'send'")
            )
            .mappings()
            .all()
        )
        return {str(r["idf_code"]).lower(): int(r["id"]) for r in rows}

    def _load_partner_ids(self, session: Session) -> set[str]:
        rows = session.execute(text("SELECT id FROM cft_partner")).mappings().all()
        return {str(r["id"]) for r in rows}

    def _load_transfer_index(
        self, session: Session
    ) -> dict[tuple[str, int, str], int]:
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
            # Keep the first match; the unique constraint on
            # (partner_id, idf_id, direct) makes duplicates unlikely here.
            if key not in out:
                out[key] = int(r["id"])
        return out
