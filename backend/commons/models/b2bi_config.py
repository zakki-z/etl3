from datetime import datetime
from sqlalchemy import (
    Table, Column,
    Integer, String, Text, DateTime, JSON,
    ForeignKey
)
from commons.base import metadata
b2bi_config_table = Table(
    "b2bi_config", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("migration_id", Integer, ForeignKey("migration.id", ondelete="CASCADE"), nullable=False, unique=True),
    Column("b2bi_partner_name", String(200)),
    Column("community_name", String(200)),
    Column("routing_id", String(200)),
    Column("transport_type", String(50)),
    Column("channel_host", String(255)),
    Column("channel_port", Integer),
    Column("agreement_rules_json", JSON),
    Column("full_config_json", JSON),
    Column("sync_status", String(30)),               # pending / synced / error
    Column("sync_error", Text),
    Column("created_at", DateTime, default=datetime.utcnow),
    extend_existing=True,
)