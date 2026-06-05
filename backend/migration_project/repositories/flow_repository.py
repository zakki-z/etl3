from __future__ import annotations

from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from migration_project.models.flow import CftFlow
from migration_project.parsers.records import FlowRecord


class FlowRepository:
    def upsert_many(self, session: Session, records: list[FlowRecord]) -> int:
        if not records:
            return 0

        # Upsert by business key (idf_code, direct) and preserve PK ids
        # because transfer.idf_id references cft_flow.id.
        by_key: dict[tuple[str, str], dict[str, str | int | None]] = {}
        for record in records:
            key = (record.idf_code, record.direct)
            current = by_key.get(key)
            if current is None:
                by_key[key] = {
                    "idf_code": record.idf_code,
                    "direct": record.direct,
                    "fcode": record.fcode,
                    "ftype": record.ftype,
                    "flrecl": record.flrecl,
                    "frecfm": record.frecfm,
                    "fname": record.fname,
                    "xlate": record.xlate,
                    "exec": record.exec,
                    "exece": record.exece,
                }
                continue

            if record.fcode is not None:
                current["fcode"] = record.fcode
            if record.ftype is not None:
                current["ftype"] = record.ftype
            if record.flrecl is not None:
                current["flrecl"] = record.flrecl
            if record.frecfm is not None:
                current["frecfm"] = record.frecfm
            if record.fname is not None:
                current["fname"] = record.fname
            current["xlate"] = record.xlate
            if record.exec is not None:
                current["exec"] = record.exec
            if record.exece is not None:
                current["exece"] = record.exece

        values = list(by_key.values())

        stmt = insert(CftFlow).values(values)
        stmt = stmt.on_duplicate_key_update(
            fcode=stmt.inserted.fcode,
            ftype=stmt.inserted.ftype,
            flrecl=stmt.inserted.flrecl,
            frecfm=stmt.inserted.frecfm,
            fname=stmt.inserted.fname,
            xlate=stmt.inserted.xlate,
            exec=stmt.inserted.exec,
            exece=stmt.inserted.exece,
        )
        session.execute(stmt)
        return len(values)
