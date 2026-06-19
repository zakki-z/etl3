from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/cft-tcp", tags=["cft-tcp"])


@router.get("")
def list_cft_tcp(db: Session = Depends(get_db)) -> list[dict]:
    """Return all CFT TCP entries."""
    rows = db.execute(
        text("SELECT partner_id, cnxout, host FROM cft_tcp")
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{partner_id}")
def get_cft_tcp(partner_id: str, db: Session = Depends(get_db)) -> dict:
    """Return the TCP entry for a single partner."""
    row = db.execute(
        text("SELECT partner_id, cnxout, host FROM cft_tcp WHERE partner_id = :pid"),
        {"pid": partner_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="CFT TCP entry not found")
    return dict(row)
