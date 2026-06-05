from datetime import datetime
from sqlalchemy import (
        Table, Column,
    Integer, String, DateTime, Float
)
from commons.base import metadata
copilot_activity_table = Table(
    "copilot_activity", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("server_name", String(100)),
    Column("partner_id_ref", String(100)),
    Column("idf", String(100)),
    Column("direction", String(10)),
    Column("last_transfer_date", DateTime),
    Column("transfer_count_12m", Integer),
    Column("avg_daily_volume", Float),
    Column("status_recommendation", String(20)),
    Column("imported_at", DateTime, default=datetime.utcnow),
    extend_existing=True,
)