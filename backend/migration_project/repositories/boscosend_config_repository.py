from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from migration_project.models.boscosend_config import BoscoSendConfig


class BoscoSendConfigRepository:
    def wipe(self, session: Session) -> int:
        """Empty the table so every run reflects the current configuration files."""
        result = session.execute(delete(BoscoSendConfig))
        return int(result.rowcount or 0)

    def insert_many(self, session: Session, rows: list[dict]) -> int:
        if not rows:
            return 0
        session.bulk_insert_mappings(BoscoSendConfig, rows)
        return len(rows)
