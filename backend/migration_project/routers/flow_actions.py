from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/flow-actions", tags=["flow-actions"])


@router.get("")
def list_flow_actions(
    script_id: int | None = Query(None, description="Filter by script"),
    scope_type: str | None = Query(None, description="Filter by scope: GLOBAL, IDF, PART, IPART, IDF_SCRIPT"),
    idf_id: int | None = Query(None, description="Filter by flow id"),
    partner_id: str | None = Query(None, description="Filter by partner"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return all flow actions with optional filters."""
    conditions = []
    params: dict = {}

    if script_id is not None:
        conditions.append("fa.script_id = :script_id")
        params["script_id"] = script_id
    if scope_type is not None:
        conditions.append("fa.scope_type = :scope_type")
        params["scope_type"] = scope_type.upper()
    if idf_id is not None:
        conditions.append("fa.idf_id = :idf_id")
        params["idf_id"] = idf_id
    if partner_id is not None:
        conditions.append("fa.partner_id = :partner_id")
        params["partner_id"] = partner_id

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = db.execute(
        text(f"""
            SELECT fa.id, fa.script_id, fa.scope_type, fa.idf_id,
                   fa.partner_id, fa.ipart_value, fa.action_order, fa.action_text,
                   f.idf_code, pps.script_name
            FROM flow_action fa
            LEFT JOIN cft_flow f ON f.id = fa.idf_id
            LEFT JOIN post_processing_scripts pps ON pps.id = fa.script_id
            {where}
            ORDER BY fa.script_id, fa.action_order
        """),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{action_id}")
def get_flow_action(action_id: int, db: Session = Depends(get_db)) -> dict:
    """Return a single flow action by id."""
    row = db.execute(
        text("""
            SELECT fa.id, fa.script_id, fa.scope_type, fa.idf_id,
                   fa.partner_id, fa.ipart_value, fa.action_order, fa.action_text,
                   f.idf_code, pps.script_name
            FROM flow_action fa
            LEFT JOIN cft_flow f ON f.id = fa.idf_id
            LEFT JOIN post_processing_scripts pps ON pps.id = fa.script_id
            WHERE fa.id = :id
        """),
        {"id": action_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Flow action not found")
    return dict(row)
