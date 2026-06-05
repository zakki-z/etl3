from __future__ import annotations

from sqlalchemy import delete, text
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from migration_project.models.partner import CftPartner
from migration_project.parsers.records import PartnerRecord


class PartnerRepository:
    def upsert_many(self, session: Session, records: list[PartnerRecord]) -> int:
        if not records:
            return 0

        # Rebuild cft_partner from latest file at each run.
        # Deduplicate by conf ID and keep last non-null values.
        by_key: dict[str, dict[str, str | int | None]] = {}
        for record in records:
            key = record.conf_id
            current = by_key.get(key)
            if current is None:
                by_key[key] = {
                    "id": record.conf_id,
                    "nspart": record.nspart,
                    "nrpart": record.nrpart,
                    "ipart": record.ipart,
                    "ssl": record.ssl,
                    "sap": record.sap,
                    "nspassw": record.nspassw,
                    "nrpassw": record.nrpassw,
                }
                continue

            current["ssl"] = record.ssl
            if record.ipart is not None:
                current["ipart"] = record.ipart
            if record.sap is not None:
                current["sap"] = record.sap
            if record.nspassw is not None:
                current["nspassw"] = record.nspassw
            if record.nrpassw is not None:
                current["nrpassw"] = record.nrpassw

        values = list(by_key.values())

        # cft_partner is referenced by cft_tcp via FK.
        # Temporarily disable FK checks for full table rebuild.
        session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        try:
            session.execute(delete(CftPartner))
            stmt = insert(CftPartner).values(values)
            session.execute(stmt)
        finally:
            session.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        return len(values)

    def get_partner_ids_by_conf_id(self, session: Session, records: list[PartnerRecord]) -> dict[str, str]:
        del session
        return {record.conf_id: record.conf_id for record in records}
