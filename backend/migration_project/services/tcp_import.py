from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from migration_project.parsers.cfttcp_parser import parse_cfttcp
from migration_project.parsers.records import TcpRecord
from migration_project.repositories.tcp_repository import TcpRepository


@dataclass(frozen=True)
class TcpImportResult:
    parsed: int
    upserted: int
    missing_partner: int
    staged_missing: int
    records: list[TcpRecord]


class TcpImportService:
    def __init__(self) -> None:
        self.repository = TcpRepository()

    def run(self, session: Session, file_path: Path, partner_id_map: dict[str, str]) -> TcpImportResult:
        records = parse_cfttcp(file_path)
        values, missing_records = self.repository.build_upsert_values(records, partner_id_map)
        upserted = self.repository.upsert_many(session, values)
        staged_missing = self.repository.upsert_missing_without_partner(session, missing_records)
        return TcpImportResult(
            parsed=len(records),
            upserted=upserted,
            missing_partner=len(missing_records),
            staged_missing=staged_missing,
            records=records,
        )
