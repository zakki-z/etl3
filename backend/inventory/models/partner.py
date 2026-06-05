from datetime import datetime
from sqlalchemy import (
    Table, Column,
    Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, UniqueConstraint
)
from commons.base import metadata
partner_table = Table(
    "partner", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("server_id", Integer, ForeignKey("server.id", ondelete="CASCADE"), nullable=False),
    Column("name", String(100), nullable=False),    # CFTPART ID
    Column("nrpart", String(100)),
    Column("nspart", String(100)),
    Column("prot", String(50)),
    Column("sap", String(20)),
    Column("state", String(50)),                    # ACTIVEBOTH / ACTIVESEND / ACTIVERECV
    Column("commut", String(10)),
    Column("idf_list", Text),                       # comma-separated IDF list from CFTPART
    Column("cfttcp_id", Integer, ForeignKey("cfttcp.id", ondelete="SET NULL"), nullable=True),
    Column("cfttcp_name", String(100)),             # raw TCP reference for debugging
    Column("comment", Text),
    Column("raw_config", Text),
    # Copilot activity enrichment
    Column("is_active", Boolean, default=True),
    Column("last_transfer_date", DateTime),
    Column("transfer_count_12m", Integer),
    Column("avg_daily_volume", Float),
    Column("activity_status", String(20)),          # ACTIVE / ACTIVE_LOW / DORMANT
    Column("created_at", DateTime, default=datetime.utcnow),
    UniqueConstraint("server_id", "name", name="uq_partner_server_name"),
    extend_existing=True,
)