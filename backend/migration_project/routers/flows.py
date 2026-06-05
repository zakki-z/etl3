from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/flows", tags=["flows"])


@router.get("")
def list_flows(
    direct: str | None = Query(None, description="Filter by direction: send or recv"),
    xlate: bool | None = Query(None, description="Filter by XLATE enabled"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return all CFT flows with optional filters."""
    conditions = []
    params: dict = {}

    if direct is not None:
        conditions.append("direct = :direct")
        params["direct"] = direct

    if xlate is True:
        conditions.append("xlate = 1")
    elif xlate is False:
        conditions.append("(xlate = 0 OR xlate IS NULL)")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = db.execute(
        text(f"""
            SELECT id, idf_code, direct, fcode, ftype, flrecl, frecfm,
                   fname, xlate, `exec`, exece
            FROM cft_flow {where}
        """),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{flow_id}")
def get_flow(flow_id: int, db: Session = Depends(get_db)) -> dict:
    """Return a single flow by id."""
    row = db.execute(
        text("""
            SELECT id, idf_code, direct, fcode, ftype, flrecl, frecfm,
                   fname, xlate, `exec`, exece
            FROM cft_flow WHERE id = :id
        """),
        {"id": flow_id},
    ).mappings().first()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Flow not found")
    return dict(row)
