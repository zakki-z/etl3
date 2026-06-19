from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/moncft-configs", tags=["moncft-configs"])


@router.get("")
def list_moncft_configs(
    transfer_id: int | None = Query(None, description="Filter by transfer id"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return all MonCFT configuration entries."""
    conditions = []
    params: dict = {}

    if transfer_id is not None:
        conditions.append("mc.transfer_id = :transfer_id")
        params["transfer_id"] = transfer_id

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = db.execute(
        text(f"""
            SELECT mc.id, mc.transfer_id, mc.fname, mc.filtre, mc.parm,
                   mc.nfname, mc.sappl AS SAPPL, mc.rappl AS RAPPL, mc.suser AS SUSER
            FROM moncft_config mc
            {where}
            ORDER BY mc.id
        """),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{config_id}")
def get_moncft_config(config_id: int, db: Session = Depends(get_db)) -> dict:
    """Return a single MonCFT config entry by id."""
    row = db.execute(
        text("""
            SELECT mc.id, mc.transfer_id, mc.fname, mc.filtre, mc.parm,
                   mc.nfname, mc.sappl AS SAPPL, mc.rappl AS RAPPL, mc.suser AS SUSER
            FROM moncft_config mc
            WHERE mc.id = :id
        """),
        {"id": config_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="MonCFT config not found")
    return dict(row)
