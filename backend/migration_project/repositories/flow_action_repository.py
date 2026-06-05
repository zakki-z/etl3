from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from migration_project.models.flow_action import FlowAction


class FlowActionRepository:
    def delete_for_script(self, session: Session, script_id: int) -> int:
        """Wipe all actions of a given script before re-inserting fresh ones."""
        result = session.execute(delete(FlowAction).where(FlowAction.script_id == script_id))
        return int(result.rowcount or 0)

    def insert_many(self, session: Session, rows: list[dict]) -> int:
        if not rows:
            return 0
        session.bulk_insert_mappings(FlowAction, rows)
        return len(rows)
