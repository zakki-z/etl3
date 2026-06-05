from datetime import datetime
from sqlalchemy import (
    Table, Column,
    Integer, String, Text, Boolean, DateTime, ForeignKey
)
from commons.base import metadata
processing_table = Table(
    "processing", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("flow_id", Integer, ForeignKey("flow.id", ondelete="CASCADE"), nullable=True),
    Column("server_id", Integer, ForeignKey("server.id", ondelete="CASCADE"), nullable=False),
    Column("script_path", String(1000), nullable=False),
    Column("script_type", String(20)),
    Column("bucket", String(1)),
    Column("classification_notes", Text),
    Column("migration_action", Text),
    Column("script_content", Text),
    Column("calls_unknown_scripts", Boolean, default=False),
    Column("unknown_script_paths", Text),
    # NEW — captures the specific if-branch condition relevant to this (flow, script) link
    # e.g. "IDF == ICSCPT AND PART == BNKFR01"
    # NULL means the script applies globally with no partner/IDF condition
    Column("branch_condition", Text),
    # NEW — the specific action taken in that branch (copy, call external, route, etc.)
    Column("branch_action", Text),
    # NEW — flags that this branch calls an external script whose purpose is unknown
    Column("branch_has_unknown_call", Boolean, default=False),
    Column("created_at", DateTime, default=datetime.utcnow),
    extend_existing=True,
)