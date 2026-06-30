from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class Community(Base):
    __tablename__ = "community"

    community_id: Mapped[str] = mapped_column(String(19), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_routing_id: Mapped[str] = mapped_column(String(19), nullable=False)
