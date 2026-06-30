from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/b2bi-partners", tags=["b2bi-partners"])

_VALID_STATUSES = {"DRAFT", "READY", "PUSHED", "VALIDATED", "MIGRATED", "ERROR"}

_SELECT_COLUMNS = """
    b2bi_partner_id, partner_code, party_name, partner_contact,
    b2bi_party_remote_id, nrpart, ssl, migration_status, nspart, community_id
"""


class StatusIn(BaseModel):
    migration_status: str


@router.get("")
def list_b2bi_partners(
    migration_status: str | None = Query(None, description="Filter by migration_status"),
    community_id: str | None = Query(None, description="Filter by community"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return all B2Bi partners, optionally filtered by status or community."""
    conditions: list[str] = []
    params: dict = {}

    if migration_status is not None:
        conditions.append("migration_status = :status")
        params["status"] = migration_status.upper()
    if community_id is not None:
        conditions.append("community_id = :community_id")
        params["community_id"] = community_id

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = db.execute(
        text(f"SELECT {_SELECT_COLUMNS} FROM b2bi_partner {where} ORDER BY party_name"),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{b2bi_partner_id}")
def get_b2bi_partner(b2bi_partner_id: int, db: Session = Depends(get_db)) -> dict:
    """Return a single B2Bi partner by id."""
    row = db.execute(
        text(f"SELECT {_SELECT_COLUMNS} FROM b2bi_partner WHERE b2bi_partner_id = :id"),
        {"id": b2bi_partner_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="B2Bi partner not found")
    return dict(row)


@router.get("/{b2bi_partner_id}/deliveries")
def list_partner_deliveries(b2bi_partner_id: int, db: Session = Depends(get_db)) -> list[dict]:
    """Return all delivery channels for a B2Bi partner."""
    rows = db.execute(
        text(
            "SELECT partner_delivery_id, friendly_name, b2bi_delivery_remote_id, host, port, "
            "parm, idf, nfname, data_encoding, record_format, record_length, fname, "
            "migration_status, b2bi_partner_id, transfer_id "
            "FROM b2bi_partner_delivery WHERE b2bi_partner_id = :id ORDER BY friendly_name"
        ),
        {"id": b2bi_partner_id},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{b2bi_partner_id}/inbound-flows")
def list_partner_inbound_flows(b2bi_partner_id: int, db: Session = Depends(get_db)) -> list[dict]:
    """Return all inbound flows for a B2Bi partner."""
    rows = db.execute(
        text(
            "SELECT inbound_flow_id, idf, fname, parm, nfname, rename_rule, "
            "migration_status, b2bi_partner_id, transfer_id "
            "FROM b2bi_inbound_flow WHERE b2bi_partner_id = :id ORDER BY idf"
        ),
        {"id": b2bi_partner_id},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.patch("/{b2bi_partner_id}/status")
def update_b2bi_partner_status(
    b2bi_partner_id: int, body: StatusIn, db: Session = Depends(get_db)
) -> dict:
    """Update a B2Bi partner's migration_status (DRAFT/READY/PUSHED/VALIDATED/MIGRATED/ERROR)."""
    new_status = body.migration_status.upper()
    if new_status not in _VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid migration_status: {new_status}")

    result = db.execute(
        text("UPDATE b2bi_partner SET migration_status = :status WHERE b2bi_partner_id = :id"),
        {"status": new_status, "id": b2bi_partner_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="B2Bi partner not found")
    db.commit()
    return {"b2bi_partner_id": b2bi_partner_id, "migration_status": new_status}
