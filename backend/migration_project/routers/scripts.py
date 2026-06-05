from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/scripts", tags=["scripts"])


@router.get("")
def list_scripts(
    server_id: str | None = Query(None, description="Filter by server"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return all post-processing scripts."""
    if server_id:
        rows = db.execute(
            text("SELECT id, server_id, script_name, script_path FROM post_processing_scripts WHERE server_id = :sid"),
            {"sid": server_id},
        ).mappings().all()
    else:
        rows = db.execute(
            text("SELECT id, server_id, script_name, script_path FROM post_processing_scripts")
        ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{script_id}/actions")
def list_script_actions(script_id: int, db: Session = Depends(get_db)) -> list[dict]:
    """Return all actions extracted from a given script."""
    rows = db.execute(
        text("""
            SELECT fa.id, fa.scope_type, fa.idf_id, fa.partner_id,
                   fa.ipart_value, fa.action_order, fa.action_text,
                   f.idf_code
            FROM flow_action fa
            LEFT JOIN cft_flow f ON f.id = fa.idf_id
            WHERE fa.script_id = :sid
            ORDER BY fa.action_order
        """),
        {"sid": script_id},
    ).mappings().all()
    return [dict(r) for r in rows]
