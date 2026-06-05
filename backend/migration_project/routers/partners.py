from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/partners", tags=["partners"])


@router.get("")
def list_partners(
    ssl: bool | None = Query(None, description="Filter by SSL enabled"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return all CFT partners, optionally filtered by SSL."""
    if ssl is True:
        rows = db.execute(
            text("SELECT id, nspart, nrpart, ipart, `ssl`, sap FROM cft_partner WHERE `ssl` = 1")
        ).mappings().all()
    elif ssl is False:
        rows = db.execute(
            text("SELECT id, nspart, nrpart, ipart, `ssl`, sap FROM cft_partner WHERE `ssl` = 0 OR `ssl` IS NULL")
        ).mappings().all()
    else:
        rows = db.execute(
            text("SELECT id, nspart, nrpart, ipart, `ssl`, sap FROM cft_partner")
        ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{partner_id}")
def get_partner(partner_id: str, db: Session = Depends(get_db)) -> dict:
    """Return a single partner with its TCP config."""
    row = db.execute(
        text("""
            SELECT p.id, p.nspart, p.nrpart, p.ipart, p.`ssl`, p.sap,
                   t.host, t.cnxout
            FROM cft_partner p
            LEFT JOIN cft_tcp t ON t.partner_id = p.id
            WHERE p.id = :id
        """),
        {"id": partner_id},
    ).mappings().first()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Partner not found")
    return dict(row)