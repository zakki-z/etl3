from datetime import datetime
from sqlalchemy import (
    Table, Column,
    Integer, String, Text, DateTime,
    ForeignKey, UniqueConstraint
)
from commons.base import metadata
cftssl_table = Table(
    "cftssl", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("server_id", Integer, ForeignKey("server.id", ondelete="CASCADE"), nullable=False),
    Column("name", String(100), nullable=False),
    Column("direct", String(20)),
    Column("rootcid", String(500)),
    Column("usercid", String(500)),
    Column("userkey", String(500)),
    Column("version", String(20)),
    Column("verify", String(20)),
    Column("ciphlist", String(500)),
    Column("raw_config", Text),
    Column("created_at", DateTime, default=datetime.utcnow),
    UniqueConstraint("server_id", "name", name="uq_cftssl_server_name"),
    extend_existing=True,
)