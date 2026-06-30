from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.models.view_base import ViewBase


class CftPartnerSslEnabled(ViewBase):
    """Read-only mapping of v_cft_partner_ssl_enabled
    (cft_partner rows filtered to ssl = 1). See view_base.py — never write
    through this model, and it's intentionally excluded from create_all()."""

    __tablename__ = "v_cft_partner_ssl_enabled"

    # Mirrors cft_partner.id, which is a real PK on the underlying table —
    # safe to reuse here since the view doesn't dedupe or aggregate rows.
    id: Mapped[str] = mapped_column(String(19), primary_key=True)
    nspart: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nrpart: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ssl: Mapped[int | None] = mapped_column(TINYINT(1), nullable=True)
    sap: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nspassw: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nrpassw: Mapped[str | None] = mapped_column(String(100), nullable=True)
