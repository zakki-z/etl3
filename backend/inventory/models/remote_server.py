from datetime import datetime
from sqlalchemy import (
    Table, Column,
    Integer, String, Text, Boolean, DateTime
)

from commons.base import metadata

remote_server_table = Table(
    "remote_server", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False, unique=True),       # friendly label, e.g. "CFT_PROD1"
    Column("remote_host", String(255), nullable=False),              # IP or hostname
    Column("remote_port", Integer, default=22),
    Column("remote_user", String(100), nullable=False),
    Column("remote_data_dir", String(1000), nullable=False),         # path on the remote server
    Column("local_dest", String(1000), nullable=True),               # local cache directory (auto-generated if blank)
    Column("auth_method", String(20), default="key"),                # key / password / agent
    Column("ssh_key_path", String(1000), nullable=True),
    Column("environment", String(50), nullable=True),                # PROD / DMZ / RECETTE
    Column("description", Text, nullable=True),
    Column("is_active", Boolean, default=True),
    Column("last_pull_at", DateTime, nullable=True),                 # timestamp of most recent successful pull
    Column("last_pull_status", String(30), nullable=True),           # success / failed
    Column("last_pull_message", Text, nullable=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    extend_existing=True,
)