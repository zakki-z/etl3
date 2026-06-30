from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.models.view_base import ViewBase


class CftFlowXlateEnabled(ViewBase):
    """Read-only mapping of v_cft_flow_xlate_enabled
    (cft_flow rows filtered to xlate = 1). See view_base.py — never write
    through this model, and it's intentionally excluded from create_all()."""

    __tablename__ = "v_cft_flow_xlate_enabled"

    # The view has no real primary key (it's a SELECT, not a table). idf_code +
    # direct mirror cft_flow's actual UniqueConstraint, so they're a safe
    # synthetic composite PK for ORM identity purposes.
    idf_code: Mapped[str] = mapped_column(String(100), primary_key=True)
    direct: Mapped[str] = mapped_column(String(100), primary_key=True)
    fcode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ftype: Mapped[str | None] = mapped_column(String(100), nullable=True)
    flrecl: Mapped[str | None] = mapped_column(String(100), nullable=True)
    frecfm: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    xlate: Mapped[int | None] = mapped_column(TINYINT(1), nullable=True)
