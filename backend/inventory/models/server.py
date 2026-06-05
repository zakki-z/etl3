from datetime import datetime
from sqlalchemy import (
     Table, Column,
    Integer, String, Text, DateTime
)
from commons.base import metadata

server_table = Table(
    "server", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False, unique=True),
    Column("ip_address", String(45)),
    Column("environment", String(50)),              # PROD / DMZ / RECETTE
    Column("install_path", String(500)),
    Column("os_info", String(200)),
    Column("raw_export_date", DateTime),
    Column("comment", Text),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    extend_existing=True,
)