from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Enum as SAEnum, Integer, TIMESTAMP, func
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GenerationJob(Base):
    __tablename__ = "generation_job"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=JobStatus.PENDING,
    )
    started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    partners_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partners_ok: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partners_blocked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
