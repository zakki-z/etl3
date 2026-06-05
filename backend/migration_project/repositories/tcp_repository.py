from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table, delete
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from migration_project.models.tcp import CftTcp
from migration_project.parsers.records import TcpRecord


class TcpRepository:
    def _staging_table(self) -> Table:
        metadata = MetaData()
        return Table(
            "stg_cft_tcp_without_partner",
            metadata,
            Column("id", String(100), primary_key=True),
            Column("cnxout", String(100)),
            Column("host", String(100)),
            Column("reason", String(255)),
        )

    def upsert_many(self, session: Session, values: list[dict[str, str | None]]) -> int:
        if not values:
            session.execute(delete(CftTcp))
            return 0

        # Rebuild cft_tcp from latest file at each run.
        # Deduplicate by partner_id and keep last non-null values.
        by_partner_id: dict[str, dict[str, str | None]] = {}
        for value in values:
            partner_id = str(value["partner_id"])  # guaranteed by caller
            current = by_partner_id.get(partner_id)
            if current is None:
                by_partner_id[partner_id] = dict(value)
                continue
            if value.get("cnxout") is not None:
                current["cnxout"] = value.get("cnxout")
            if value.get("host") is not None:
                current["host"] = value.get("host")

        session.execute(delete(CftTcp))
        stmt = insert(CftTcp).values(list(by_partner_id.values()))
        session.execute(stmt)
        return len(values)

    def build_upsert_values(
        self,
        tcp_records: list[TcpRecord],
        partner_id_map: dict[str, str],
    ) -> tuple[list[dict[str, str | None]], list[TcpRecord]]:
        values: list[dict[str, str | None]] = []
        missing_records: list[TcpRecord] = []

        for record in tcp_records:
            partner_id = partner_id_map.get(record.conf_id)
            if not partner_id:
                missing_records.append(record)
                continue

            values.append(
                {
                    "partner_id": partner_id,
                    "cnxout": record.cnxout,
                    "host": record.host,
                }
            )

        return values, missing_records

    def upsert_missing_without_partner(self, session: Session, missing_records: list[TcpRecord]) -> int:
        stg = self._staging_table()
        # Ensure staging table exists even if SQL bootstrap script was not run yet.
        stg.create(bind=session.get_bind(), checkfirst=True)

        # Rebuild staging table from latest file at each run.
        session.execute(delete(stg))
        if not missing_records:
            return 0

        values_by_conf_id: dict[str, dict[str, str | None]] = {}
        for r in missing_records:
            current = values_by_conf_id.get(r.conf_id)
            if current is None:
                values_by_conf_id[r.conf_id] = {
                    "id": r.conf_id,
                    "cnxout": r.cnxout,
                    "host": r.host,
                    "reason": "missing_partner_mapping",
                }
                continue
            if r.cnxout is not None:
                current["cnxout"] = r.cnxout
            if r.host is not None:
                current["host"] = r.host

        values = [
            {
                "id": value["id"],
                "cnxout": value["cnxout"],
                "host": value["host"],
                "reason": "missing_partner_mapping",
            }
            for value in values_by_conf_id.values()
        ]

        stmt = insert(stg).values(values)
        session.execute(stmt)
        return len(values)
