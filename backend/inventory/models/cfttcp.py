from datetime import datetime
from sqlalchemy import (
     Table, Column,
    Integer, String, Text, DateTime, UniqueConstraint, ForeignKey
)

from commons.base import metadata

cfttcp_table = Table(
    "cfttcp", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("server_id", Integer, ForeignKey("server.id", ondelete="CASCADE"), nullable=False),
    Column("name", String(100), nullable=False),    # CFTTCP ID
    Column("host", String(255)),
    Column("port", Integer),
    Column("cnx_in", Integer),
    Column("cnx_out", Integer),
    Column("cnx_inout", Integer),
    Column("retry_wait", Integer),                  # RETRYW
    Column("retry_max", Integer),                   # RETRY
    Column("ssl_id", String(100)),
    Column("comment", Text),
    Column("raw_config", Text),
    Column("created_at", DateTime, default=datetime.utcnow),
    UniqueConstraint("server_id", "name", name="uq_cfttcp_server_name"),
    extend_existing=True,
)