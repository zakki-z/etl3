from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from migration_project.models.exception_log import ExceptionLog, ExceptionSeverity


class ExceptionLogRepository:
    def insert_many(self, session: Session, rows: list[dict]) -> int:
        if not rows:
            return 0
        session.bulk_insert_mappings(ExceptionLog, rows)
        return len(rows)

    def get_by_job(
        self,
        session: Session,
        job_id: int,
        *,
        severity: str | None = None,
        resolved: bool | None = None,
    ) -> list[ExceptionLog]:
        q = select(ExceptionLog).where(ExceptionLog.job_id == job_id)
        if severity is not None:
            q = q.where(ExceptionLog.severity == severity.upper())
        if resolved is not None:
            q = q.where(ExceptionLog.resolved == (1 if resolved else 0))
        q = q.order_by(ExceptionLog.severity, ExceptionLog.id)
        return list(session.execute(q).scalars().all())

    def resolve(
        self,
        session: Session,
        exception_id: int,
        *,
        note: str | None = None,
    ) -> bool:
        exc = session.get(ExceptionLog, exception_id)
        if exc is None:
            return False
        exc.resolved = 1
        exc.resolved_at = datetime.now(UTC).replace(tzinfo=None)
        exc.resolution_note = note
        return True

    def count_blocking_unresolved(self, session: Session, job_id: int) -> int:
        rows = session.execute(
            select(ExceptionLog).where(
                ExceptionLog.job_id == job_id,
                ExceptionLog.severity == ExceptionSeverity.BLOCKING,
                ExceptionLog.resolved == 0,
            )
        ).scalars().all()
        return len(rows)
