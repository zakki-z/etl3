from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from migration_project.models.moncft_config import MonCftConfig


class MonCftConfigRepository:
    def wipe(self, session: Session) -> int:
        """Empty the table so we can re-insert a fresh snapshot."""
        result = session.execute(delete(MonCftConfig))
        return int(result.rowcount or 0)

    def insert_many(self, session: Session, rows: list[dict]) -> int:
        if not rows:
            return 0
        session.bulk_insert_mappings(MonCftConfig, rows)
        return len(rows)
