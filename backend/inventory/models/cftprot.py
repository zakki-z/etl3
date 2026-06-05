from datetime import datetime
from sqlalchemy import (
    Table, Column,
    Integer, String, Text, DateTime,
    ForeignKey, UniqueConstraint
)
from commons.base import metadata
# Protocol and SSL tables (bonus — captures CFTPROT and CFTSSL blocks)
cftprot_table = Table(
    "cftprot", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("server_id", Integer, ForeignKey("server.id", ondelete="CASCADE"), nullable=False),
    Column("name", String(100), nullable=False),
    Column("prot_type", String(50)),
    Column("net", String(100)),
    Column("sap", String(20)),
    Column("ssl_id", String(100)),
    Column("compress", String(10)),
    Column("restart", String(10)),
    Column("concat", String(10)),
    Column("comment", Text),
    Column("raw_config", Text),
    Column("created_at", DateTime, default=datetime.utcnow),
    UniqueConstraint("server_id", "name", name="uq_cftprot_server_name"),
    extend_existing=True,
)