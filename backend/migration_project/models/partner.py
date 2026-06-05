from __future__ import annotations

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class CftPartner(Base):
    __tablename__ = "cft_partner"
    __table_args__ = (UniqueConstraint("nspart", "nrpart", name="uq_cft_partner_nspart_nrpart"),)

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    nspart: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nrpart: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ipart: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ssl: Mapped[int | None] = mapped_column(TINYINT(1), nullable=True)
    sap: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nspassw: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nrpassw: Mapped[str | None] = mapped_column(String(100), nullable=True)
