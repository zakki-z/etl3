from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class MonCftConfig(Base):
    __tablename__ = "moncft_config"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    transfer_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("transfer.id"), nullable=True
    )
    fname: Mapped[str | None] = mapped_column(String(500), nullable=True)
    filtre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parm: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nfname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sappl: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rappl: Mapped[str | None] = mapped_column(String(100), nullable=True)
    suser: Mapped[str | None] = mapped_column(String(100), nullable=True)
