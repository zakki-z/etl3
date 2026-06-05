from datetime import datetime
from sqlalchemy import (
    Table, Column,
    Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, UniqueConstraint,
)
from commons.base import metadata
flow_table = Table(
    "flow", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("partner_id", Integer, ForeignKey("partner.id", ondelete="CASCADE"), nullable=False),
    Column("server_id", Integer, ForeignKey("server.id", ondelete="CASCADE"), nullable=False),
    Column("idf", String(100), nullable=False),
    Column("cft_type", String(10), nullable=False), # SEND / RECV
    Column("ftype", String(10)),
    Column("fcode", String(20)),
    Column("fname", String(1000)),
    Column("wfname", String(1000)),
    Column("nfname", String(1000)),
    Column("exec", String(1000)),                   # EXEC field from CFTSEND/CFTRECV
    Column("comment", Text),
    Column("raw_config", Text),
    # Copilot activity enrichment
    Column("is_active", Boolean, default=True),
    Column("last_transfer_date", DateTime),
    Column("transfer_count_12m", Integer),
    Column("avg_daily_volume", Float),
    Column("activity_status", String(20)),
    # partner list (for multi-partner flows like SEPAXML)
    Column("partner_list", Text),                   # raw PART value e.g. "(BNKFR01,SGENPRD,BNPPRD)"
    Column("created_at", DateTime, default=datetime.utcnow),
    UniqueConstraint("partner_id", "idf", "cft_type", name="uq_flow_partner_idf_type"),
    extend_existing=True,
)