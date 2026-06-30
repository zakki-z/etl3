from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/b2bi-partner-deliveries", tags=["b2bi-partner-deliveries"])

_VALID_STATUSES = {"DRAFT", "READY", "PUSHED", "VALIDATED", "MIGRATED", "ERROR"}

_SELECT_COLUMNS = """
    partner_delivery_id, friendly_name, b2bi_delivery_remote_id, host, port,
    parm, idf, nfname, data_encoding, record_format, record_length, fname,
    migration_status, b2bi_partner_id, transfer_id
"""


class StatusIn(BaseModel):
    migration_status: str


@router.get("")
def list_deliveries(
    migration_status: str | None = Query(None, description="Filter by migration_status"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return all B2Bi partner deliveries, optionally filtered by status."""
    if migration_status is not None:
        rows = db.execute(
            text(f"SELECT {_SELECT_COLUMNS} FROM b2bi_partner_delivery WHERE migration_status = :status"),
            {"status": migration_status.upper()},
        ).mappings().all()
    else:
        rows = db.execute(
            text(f"SELECT {_SELECT_COLUMNS} FROM b2bi_partner_delivery")
        ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{partner_delivery_id}")
def get_delivery(partner_delivery_id: int, db: Session = Depends(get_db)) -> dict:
    """Return a single delivery by id."""
    row = db.execute(
        text(f"SELECT {_SELECT_COLUMNS} FROM b2bi_partner_delivery WHERE partner_delivery_id = :id"),
        {"id": partner_delivery_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return dict(row)


@router.get("/by-transfer/{transfer_id}")
def get_delivery_by_transfer(transfer_id: int, db: Session = Depends(get_db)) -> dict:
    """Return the delivery row for a given transfer (transfer_id is unique on this table)."""
    row = db.execute(
        text(f"SELECT {_SELECT_COLUMNS} FROM b2bi_partner_delivery WHERE transfer_id = :id"),
        {"id": transfer_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="No delivery found for this transfer")
    return dict(row)


@router.patch("/{partner_delivery_id}/status")
def update_delivery_status(
    partner_delivery_id: int, body: StatusIn, db: Session = Depends(get_db)
) -> dict:
    """Update a delivery's migration_status."""
    new_status = body.migration_status.upper()
    if new_status not in _VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid migration_status: {new_status}")

    result = db.execute(
        text(
            "UPDATE b2bi_partner_delivery SET migration_status = :status "
            "WHERE partner_delivery_id = :id"
        ),
        {"status": new_status, "id": partner_delivery_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Delivery not found")
    db.commit()
    return {"partner_delivery_id": partner_delivery_id, "migration_status": new_status}
