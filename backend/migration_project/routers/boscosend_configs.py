from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/boscosend-configs", tags=["boscosend-configs"])


@router.get("")
def list_boscosend_configs(
    transfer_id: int | None = Query(None, description="Filter by transfer id"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return all BoscoSend configuration entries."""
    conditions = []
    params: dict = {}

    if transfer_id is not None:
        conditions.append("bc.transfer_id = :transfer_id")
        params["transfer_id"] = transfer_id

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = db.execute(
        text(f"""
            SELECT bc.id, bc.remote_address, bc.remote_subdir, bc.transfer_id,
                   bc.localdir, bc.backup_dir, bc.file_search_mask, bc.nom_section,
                   bc.`Cmdb-Prestation`
            FROM boscosend_config bc
            {where}
            ORDER BY bc.id
        """),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{config_id}")
def get_boscosend_config(config_id: int, db: Session = Depends(get_db)) -> dict:
    """Return a single BoscoSend config entry by id."""
    row = db.execute(
        text("""
            SELECT bc.id, bc.remote_address, bc.remote_subdir, bc.transfer_id,
                   bc.localdir, bc.backup_dir, bc.file_search_mask, bc.nom_section,
                   bc.`Cmdb-Prestation`
            FROM boscosend_config bc
            WHERE bc.id = :id
        """),
        {"id": config_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="BoscoSend config not found")
    return dict(row)
