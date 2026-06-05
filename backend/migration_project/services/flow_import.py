from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from migration_project.parsers.cftflow_parser import parse_cftrecv, parse_cftsend
from migration_project.parsers.records import FlowRecord
from migration_project.repositories.flow_repository import FlowRepository


@dataclass(frozen=True)
class FlowImportResult:
    send_parsed: int
    recv_parsed: int
    upserted: int
    records: list[FlowRecord]


class FlowImportService:
    def __init__(self) -> None:
        self.repository = FlowRepository()

    def run(self, session: Session, file_path: Path) -> FlowImportResult:
        send_records = parse_cftsend(file_path)
        recv_records = parse_cftrecv(file_path)
        records = [*send_records, *recv_records]
        upserted = self.repository.upsert_many(session, records)
        return FlowImportResult(
            send_parsed=len(send_records),
            recv_parsed=len(recv_records),
            upserted=upserted,
            records=records,
        )
