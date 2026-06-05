from __future__ import annotations

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class ActionScope(str, enum.Enum):
    GLOBAL = "GLOBAL"
    IDF = "IDF"
    PART = "PART"
    IPART = "IPART"
    IDF_SCRIPT = "IDF_SCRIPT"


class FlowAction(Base):
    __tablename__ = "flow_action"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    script_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("post_processing_scripts.id"),
        nullable=False,
    )
    scope_type: Mapped[ActionScope] = mapped_column(
        Enum(ActionScope, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    idf_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("cft_flow.id"), nullable=True
    )
    partner_id: Mapped[str | None] = mapped_column(
        String(19), ForeignKey("cft_partner.id"), nullable=True
    )
    ipart_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    action_text: Mapped[str] = mapped_column(String(2000), nullable=False)
