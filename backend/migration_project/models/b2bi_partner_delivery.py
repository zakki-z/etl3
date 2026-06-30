from __future__ import annotations

from sqlalchemy import Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base
from migration_project.models.b2bi_partner import MigrationStatus


class B2biPartnerDelivery(Base):
    __tablename__ = "b2bi_partner_delivery"

    partner_delivery_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), primary_key=True, autoincrement=True
    )
    friendly_name: Mapped[str] = mapped_column(String(255), nullable=False)
    b2bi_delivery_remote_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    port: Mapped[str | None] = mapped_column(String(100), nullable=True)
    parm: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idf: Mapped[str] = mapped_column(String(100), nullable=False)
    nfname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_encoding: Mapped[str | None] = mapped_column(String(50), nullable=True)
    record_format: Mapped[str | None] = mapped_column(String(100), nullable=True)
    record_length: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fname: Mapped[str | None] = mapped_column(String(500), nullable=True)
    migration_status: Mapped[MigrationStatus] = mapped_column(
        SAEnum(MigrationStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=MigrationStatus.DRAFT,
    )
    b2bi_partner_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("b2bi_partner.b2bi_partner_id"), nullable=False
    )
    # UNI in DB: one delivery row per transfer.
    transfer_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("transfer.id"), nullable=False, unique=True
    )
