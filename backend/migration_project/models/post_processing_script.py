from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class PostProcessingScript(Base):
    __tablename__ = "post_processing_scripts"
    __table_args__ = (
        UniqueConstraint("server_id", "script_path", name="uq_script_per_server"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    server_id: Mapped[str] = mapped_column(
        String(19), ForeignKey("server.id"), nullable=False
    )
    script_path: Mapped[str] = mapped_column(String(500), nullable=False)
    script_name: Mapped[str] = mapped_column(String(255), nullable=False)
