from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/transfers", tags=["transfers"])


@router.get("")
def list_transfers(
    server_id: str | None = Query(None, description="Filter by server"),
    partner_id: str | None = Query(None, description="Filter by partner"),
    statut: str | None = Query(None, description="Filter by status: OK or NOK"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return transfers with optional filters."""
    conditions = []
    params: dict = {}

    if server_id:
        conditions.append("t.server_id = :server_id")
        params["server_id"] = server_id
    if partner_id:
        conditions.append("t.partner_id = :partner_id")
        params["partner_id"] = partner_id
    if statut:
        conditions.append("t.statut = :statut")
        params["statut"] = statut.upper()

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = db.execute(
        text(f"""
            SELECT t.id, t.partner_id, t.idf_id, t.date, t.direct,
                   t.server_id, t.statut,
                   f.idf_code
            FROM transfer t
            LEFT JOIN cft_flow f ON f.id = t.idf_id
            {where}
            ORDER BY t.date DESC
        """),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{transfer_id}")
def get_transfer(transfer_id: int, db: Session = Depends(get_db)) -> dict:
    """Return a single transfer by id."""
    row = db.execute(
        text("""
            SELECT t.id, t.partner_id, t.idf_id, t.date, t.direct,
                   t.server_id, t.statut, f.idf_code
            FROM transfer t
            LEFT JOIN cft_flow f ON f.id = t.idf_id
            WHERE t.id = :id
        """),
        {"id": transfer_id},
    ).mappings().first()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Transfer not found")
    return dict(row)
