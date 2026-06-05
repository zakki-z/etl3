from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from migration_project.db import Base


class Server(Base):
    __tablename__ = "server"

    id: Mapped[str] = mapped_column(String(19), primary_key=True)
    host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    environment: Mapped[str | None] = mapped_column(String(100), nullable=True)
