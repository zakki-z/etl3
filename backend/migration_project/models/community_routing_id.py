from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class CommunityRoutingId(Base):
    __tablename__ = "community_routing_ids"

    routing_id: Mapped[str] = mapped_column(String(19), primary_key=True)
    community_id: Mapped[str] = mapped_column(
        String(19), ForeignKey("community.community_id"), nullable=False
    )
