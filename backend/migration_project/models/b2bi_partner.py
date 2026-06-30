from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import BIGINT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class MigrationStatus(str, enum.Enum):
    """Per-row migration lifecycle, shared by b2bi_partner, b2bi_partner_delivery,
    and b2bi_inbound_flow. Replaces the old job/exception-based tracking from the
    retired Phase 2 generation engine (mapping_rule / generation_job / b2bi_config)."""

    DRAFT = "DRAFT"
    READY = "READY"
    PUSHED = "PUSHED"
    VALIDATED = "VALIDATED"
    MIGRATED = "MIGRATED"
    ERROR = "ERROR"


class B2biPartner(Base):
    __tablename__ = "b2bi_partner"

    b2bi_partner_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), primary_key=True, autoincrement=True
    )
    partner_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    party_name: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_contact: Mapped[str | None] = mapped_column(Text, nullable=True)
    b2bi_party_remote_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nrpart: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ssl: Mapped[int | None] = mapped_column(TINYINT(1), nullable=True)
    migration_status: Mapped[MigrationStatus] = mapped_column(
        SAEnum(MigrationStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=MigrationStatus.DRAFT,
    )
    nspart: Mapped[str | None] = mapped_column(String(19), nullable=True)
    community_id: Mapped[str] = mapped_column(
        String(19), ForeignKey("community.community_id"), nullable=False
    )
