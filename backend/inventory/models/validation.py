from datetime import datetime
from sqlalchemy import (
    Table, Column,
    Integer, String, Boolean, DateTime, JSON,
    ForeignKey
)
from commons.base import metadata
validation_table = Table(
    "validation", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("migration_id", Integer, ForeignKey("migration.id", ondelete="CASCADE"), nullable=False),
    Column("test_file", String(500)),
    Column("status", String(30)),                    # pending / passed / failed
    Column("checksums_match", Boolean),
    Column("discrepancies_json", JSON),
    Column("validated_by", String(100)),
    Column("validated_at", DateTime),
    Column("created_at", DateTime, default=datetime.utcnow),
    extend_existing=True,
)