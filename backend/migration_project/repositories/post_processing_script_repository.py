from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from migration_project.models.post_processing_script import PostProcessingScript


class PostProcessingScriptRepository:
    def upsert(
        self,
        session: Session,
        *,
        server_id: str,
        script_path: str,
        script_name: str,
    ) -> int:
        """Insert or update a script row, then return its id (PK)."""
        stmt = insert(PostProcessingScript).values(
            server_id=server_id,
            script_path=script_path,
            script_name=script_name,
        )
        stmt = stmt.on_duplicate_key_update(script_name=stmt.inserted.script_name)
        session.execute(stmt)
        session.flush()

        row_id = session.execute(
            select(PostProcessingScript.id).where(
                PostProcessingScript.server_id == server_id,
                PostProcessingScript.script_path == script_path,
            )
        ).scalar_one()
        return int(row_id)
