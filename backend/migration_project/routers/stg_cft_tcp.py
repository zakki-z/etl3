from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/stg-cft-tcp-without-partner", tags=["staging"])


@router.get("")
def list_stg_cft_tcp_without_partner(db: Session = Depends(get_db)) -> list[dict]:
    """Return all CFTTCP entries that could not be matched to a partner."""
    rows = db.execute(
        text("SELECT id, cnxout, host, reason FROM stg_cft_tcp_without_partner ORDER BY id")
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{entry_id}")
def get_stg_cft_tcp_without_partner(entry_id: str, db: Session = Depends(get_db)) -> dict:
    """Return a single unmatched TCP entry by its conf id."""
    row = db.execute(
        text("SELECT id, cnxout, host, reason FROM stg_cft_tcp_without_partner WHERE id = :id"),
        {"id": entry_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Staging entry not found")
    return dict(row)
