from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Enum as SAEnum, ForeignKey, String, TIMESTAMP, func
from sqlalchemy.dialects.mysql import BIGINT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class ExceptionSeverity(str, enum.Enum):
    BLOCKING = "BLOCKING"
    WARNING = "WARNING"


class ExceptionLog(Base):
    __tablename__ = "exception_log"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("generation_job.id"), nullable=False
    )
    partner_id: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[ExceptionSeverity] = mapped_column(
        SAEnum(ExceptionSeverity, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    exception_type: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    resolved: Mapped[int] = mapped_column(TINYINT(1), nullable=False, default=0)
    resolved_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
