from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from migration_project.models.b2bi_config import B2biConfig, SyncStatus


class B2biConfigRepository:
    def insert_many(self, session: Session, rows: list[dict]) -> int:
        if not rows:
            return 0
        stmt = insert(B2biConfig).values(rows)
        stmt = stmt.on_duplicate_key_update(
            payload=stmt.inserted.payload,
            sync_status=stmt.inserted.sync_status,
            generated_at=stmt.inserted.generated_at,
        )
        session.execute(stmt)
        return len(rows)

    def get_by_job(
        self,
        session: Session,
        job_id: int,
        *,
        sync_status: str | None = None,
    ) -> list[B2biConfig]:
        q = select(B2biConfig).where(B2biConfig.job_id == job_id)
        if sync_status is not None:
            q = q.where(B2biConfig.sync_status == sync_status.upper())
        return list(session.execute(q).scalars().all())

    def get_by_id(self, session: Session, config_id: int) -> B2biConfig | None:
        return session.get(B2biConfig, config_id)

    def approve(self, session: Session, config_id: int) -> bool:
        config = session.get(B2biConfig, config_id)
        if config is None:
            return False
        config.sync_status = SyncStatus.APPROVED
        config.approved_at = datetime.now(UTC).replace(tzinfo=None)
        return True
