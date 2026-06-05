from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from migration_project.parsers.cftpart_parser import parse_cftpart
from migration_project.parsers.records import PartnerRecord
from migration_project.repositories.partner_repository import PartnerRepository


@dataclass(frozen=True)
class PartnerImportResult:
    parsed: int
    upserted: int
    records: list[PartnerRecord]
    partner_id_by_conf_id: dict[str, str]


class PartnerImportService:
    def __init__(self) -> None:
        self.repository = PartnerRepository()

    def run(self, session: Session, file_path: Path) -> PartnerImportResult:
        records = parse_cftpart(file_path)
        upserted = self.repository.upsert_many(session, records)
        partner_map = self.repository.get_partner_ids_by_conf_id(session, records)
        return PartnerImportResult(
            parsed=len(records),
            upserted=upserted,
            records=records,
            partner_id_by_conf_id=partner_map,
        )
