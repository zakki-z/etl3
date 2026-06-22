from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Enum as SAEnum, String, TIMESTAMP, func
from sqlalchemy.dialects.mysql import BIGINT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class MappingRule(Base):
    __tablename__ = "mapping_rule"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    source_field: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_field: Mapped[str] = mapped_column(String(255), nullable=False)
    transform_type: Mapped[str] = mapped_column(
        SAEnum("direct", "static", "lookup", "template", name="transform_type_enum"),
        nullable=False,
        default="direct",
    )
    transform_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[int] = mapped_column(TINYINT(1), nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
