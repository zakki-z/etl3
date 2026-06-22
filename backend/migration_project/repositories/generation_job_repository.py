from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from migration_project.models.generation_job import GenerationJob, JobStatus


class GenerationJobRepository:
    def create(self, session: Session) -> GenerationJob:
        """Insert a new job in PENDING state and return it."""
        job = GenerationJob(status=JobStatus.PENDING)
        session.add(job)
        session.flush()
        return job

    def get_by_id(self, session: Session, job_id: int) -> GenerationJob | None:
        return session.get(GenerationJob, job_id)

    def list_all(self, session: Session, limit: int = 50) -> list[GenerationJob]:
        return list(
            session.execute(
                select(GenerationJob).order_by(GenerationJob.id.desc()).limit(limit)
            ).scalars().all()
        )

    def mark_in_progress(self, session: Session, job: GenerationJob) -> None:
        job.status = JobStatus.IN_PROGRESS
        job.started_at = datetime.now(UTC).replace(tzinfo=None)

    def mark_completed(
        self,
        session: Session,
        job: GenerationJob,
        *,
        partners_total: int,
        partners_ok: int,
        partners_blocked: int,
    ) -> None:
        job.status = JobStatus.COMPLETED
        job.finished_at = datetime.now(UTC).replace(tzinfo=None)
        job.partners_total = partners_total
        job.partners_ok = partners_ok
        job.partners_blocked = partners_blocked

    def mark_failed(self, session: Session, job: GenerationJob) -> None:
        job.status = JobStatus.FAILED
        job.finished_at = datetime.now(UTC).replace(tzinfo=None)
