
from __future__ import annotations


import enum
from datetime import date as dt_date


from sqlalchemy import Date, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column


from migration_project.db import Base




class TransferStatut(str, enum.Enum):
    OK = "OK"
    NOK = "NOK"




class Transfer(Base):
    __tablename__ = "transfer"
    __table_args__ = (
        UniqueConstraint("partner_id", "idf_id", "direct", name="uq_transfert_partner_idf_direct"),
    )


    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    partner_id: Mapped[str | None] = mapped_column(
        String(19), ForeignKey("cft_partner.id"), nullable=True
    )
    idf_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("cft_flow.id"), nullable=False)
    date: Mapped[dt_date | None] = mapped_column(Date(), nullable=True)
    direct: Mapped[str | None] = mapped_column(String(100), nullable=True)
    server_id: Mapped[str | None] = mapped_column(
        String(19), ForeignKey("server.id"), nullable=True
    )
    statut: Mapped[TransferStatut | None] = mapped_column(
        Enum(TransferStatut, values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )


