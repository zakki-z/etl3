from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from migration_project.db import session_scope
from migration_project.parsers.cftflow_parser import parse_cftrecv, parse_cftsend
from migration_project.parsers.cftpart_parser import parse_cftpart
from migration_project.parsers.cfttcp_parser import parse_cfttcp
from migration_project.services.flow_import import FlowImportService
from migration_project.services.partner_import import PartnerImportService
from migration_project.services.tcp_import import TcpImportService


@dataclass(frozen=True)
class ImportReport:
    file_path: str
    files_processed: int
    partner_parsed: int
    partner_upserted: int
    tcp_parsed: int
    tcp_upserted: int
    tcp_missing_partner: int
    tcp_staged_missing: int
    send_parsed: int
    recv_parsed: int
    flow_upserted: int


class ImportService:
    def __init__(self) -> None:
        self.partner_import = PartnerImportService()
        self.tcp_import = TcpImportService()
        self.flow_import = FlowImportService()

    def run(self, file_path: Path) -> ImportReport:
        return self.run_many([file_path])

    def run_many(self, file_paths: list[Path]) -> ImportReport:
        if not file_paths:
            raise ValueError("No configuration files to import.")

        partner_records = []
        tcp_records = []
        send_records = []
        recv_records = []
        for file_path in file_paths:
            partner_records.extend(parse_cftpart(file_path))
            tcp_records.extend(parse_cfttcp(file_path))
            send_records.extend(parse_cftsend(file_path))
            recv_records.extend(parse_cftrecv(file_path))

        with session_scope() as session:
            partner_upserted = self.partner_import.repository.upsert_many(session, partner_records)
            partner_map = self.partner_import.repository.get_partner_ids_by_conf_id(session, partner_records)

            tcp_values, tcp_missing = self.tcp_import.repository.build_upsert_values(tcp_records, partner_map)
            tcp_upserted = self.tcp_import.repository.upsert_many(session, tcp_values)
            tcp_staged = self.tcp_import.repository.upsert_missing_without_partner(session, tcp_missing)

            flow_records = [*send_records, *recv_records]
            flow_upserted = self.flow_import.repository.upsert_many(session, flow_records)

        return ImportReport(
            file_path=f"{file_paths[0]} -> {file_paths[-1]}",
            files_processed=len(file_paths),
            partner_parsed=len(partner_records),
            partner_upserted=partner_upserted,
            tcp_parsed=len(tcp_records),
            tcp_upserted=tcp_upserted,
            tcp_missing_partner=len(tcp_missing),
            tcp_staged_missing=tcp_staged,
            send_parsed=len(send_records),
            recv_parsed=len(recv_records),
            flow_upserted=flow_upserted,
        )
