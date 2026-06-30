from __future__ import annotations

from sqlalchemy import Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base
from migration_project.models.b2bi_partner import MigrationStatus


class B2biInboundFlow(Base):
    __tablename__ = "b2bi_inbound_flow"

    inbound_flow_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), primary_key=True, autoincrement=True
    )
    idf: Mapped[str] = mapped_column(String(100), nullable=False)
    fname: Mapped[str | None] = mapped_column(String(500), nullable=True)
    parm: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nfname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rename_rule: Mapped[str | None] = mapped_column(String(500), nullable=True)
    migration_status: Mapped[MigrationStatus] = mapped_column(
        SAEnum(MigrationStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=MigrationStatus.DRAFT,
    )
    b2bi_partner_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("b2bi_partner.b2bi_partner_id"), nullable=False
    )
    # UNI in DB: one inbound flow row per transfer.
    transfer_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("transfer.id"), nullable=False, unique=True
    )
