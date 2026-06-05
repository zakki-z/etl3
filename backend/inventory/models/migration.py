from datetime import datetime
from sqlalchemy import (
    Table, Column,
    Integer, String, Text, DateTime,
    ForeignKey
)
from commons.base import metadata
migration_table = Table(
    "migration", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("flow_id", Integer, ForeignKey("flow.id", ondelete="CASCADE"), nullable=False, unique=True),
    Column("status", String(30), default="pending"),    # pending / in_progress / validated / deployed / skipped
    Column("complexity", String(20)),                   # low / medium / high
    Column("assigned_to", String(100)),
    Column("exception_notes", Text),
    Column("started_at", DateTime),
    Column("completed_at", DateTime),
    Column("last_updated", DateTime, default=datetime.utcnow),
    extend_existing=True,
)