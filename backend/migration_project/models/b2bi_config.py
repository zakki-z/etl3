from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Enum as SAEnum, ForeignKey, JSON, String, TIMESTAMP, func
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class SyncStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DEPLOYED = "DEPLOYED"
    FAILED = "FAILED"


class B2biConfig(Base):
    __tablename__ = "b2bi_config"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("generation_job.id"), nullable=False
    )
    partner_id: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    sync_status: Mapped[SyncStatus] = mapped_column(
        SAEnum(SyncStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=SyncStatus.PENDING,
    )
    generated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    approved_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
