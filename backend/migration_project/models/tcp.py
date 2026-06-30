from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class CftTcp(Base):
    __tablename__ = "cft_tcp"

    partner_id: Mapped[str] = mapped_column(String(19), ForeignKey("cft_partner.id"), primary_key=True)
    # DB column is `cnxout` (value comes from conf `CNXOUT`).
    cnxout: Mapped[str | None] = mapped_column(String(100), nullable=True)
    host: Mapped[str | None] = mapped_column(String(100), nullable=True)
