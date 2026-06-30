from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class BoscoSendConfig(Base):
    __tablename__ = "boscosend_config"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    remote_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remote_subdir: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transfer_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True), ForeignKey("transfer.id"), nullable=True
    )
    localdir: Mapped[str | None] = mapped_column(String(255), nullable=True)
    backup_dir: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_search_mask: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nom_section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cmdb_prestation: Mapped[str | None] = mapped_column(
        "Cmdb-Prestation", String(100), nullable=True
    )
