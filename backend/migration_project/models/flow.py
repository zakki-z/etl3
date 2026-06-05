from __future__ import annotations

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class CftFlow(Base):
    __tablename__ = "cft_flow"
    __table_args__ = (UniqueConstraint("idf_code", "direct", name="uq_cft_flow_idf_direct"),)

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    idf_code: Mapped[str] = mapped_column(String(100), nullable=False)
    direct: Mapped[str] = mapped_column(String(100), nullable=False)
    fcode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ftype: Mapped[str | None] = mapped_column(String(100), nullable=True)
    flrecl: Mapped[str | None] = mapped_column(String(100), nullable=True)
    frecfm: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    xlate: Mapped[int | None] = mapped_column(TINYINT(1), nullable=True)
    exec: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    exece: Mapped[str | None] = mapped_column(String(1000), nullable=True)
