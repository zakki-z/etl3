from datetime import datetime
from sqlalchemy import (
    Table, Column,
    Integer, String, Text, Boolean, DateTime,
    ForeignKey, UniqueConstraint
)
from commons.base import metadata
bosco_route_table = Table(
    "bosco_route", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("server_id", Integer, ForeignKey("server.id", ondelete="CASCADE"), nullable=False),
    Column("flow_id", Integer, ForeignKey("flow.id", ondelete="SET NULL"), nullable=True),
    Column("section_name", String(200), nullable=False),
    Column("route_type", String(20), nullable=False),   # BOSCO_SEND / BOSCO_RECV
    Column("active", Boolean, default=True),
    Column("local_dir", String(1000)),
    Column("backup_dir", String(1000)),
    Column("dest_dir", String(1000)),               # BOSCO_RECV only
    Column("archive_dir", String(1000)),            # BOSCO_RECV only
    Column("remote_address", String(255)),           # BOSCO_SEND only
    Column("remote_port", Integer),                  # BOSCO_SEND only
    Column("remote_subdir", String(500)),             # BOSCO_SEND only
    Column("file_mask", String(200)),
    Column("protocol", String(50)),
    Column("partner_ref", String(100)),              # PARTNER field from Bosco Send
    Column("idf_ref", String(100)),                  # IDF field from Bosco Send
    Column("schedule", String(100)),
    Column("processing_app", String(200)),           # BOSCO_RECV only
    Column("comment", Text),
    Column("raw_config", Text),
    Column("created_at", DateTime, default=datetime.utcnow),
    UniqueConstraint("server_id", "section_name", "route_type", name="uq_bosco_server_section_type"),
    extend_existing=True,
)