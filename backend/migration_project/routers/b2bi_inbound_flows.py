from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/b2bi-inbound-flows", tags=["b2bi-inbound-flows"])

_VALID_STATUSES = {"DRAFT", "READY", "PUSHED", "VALIDATED", "MIGRATED", "ERROR"}

_SELECT_COLUMNS = """
    inbound_flow_id, idf, fname, parm, nfname, rename_rule,
    migration_status, b2bi_partner_id, transfer_id
"""


class StatusIn(BaseModel):
    migration_status: str


@router.get("")
def list_inbound_flows(
    migration_status: str | None = Query(None, description="Filter by migration_status"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return all B2Bi inbound flows, optionally filtered by status."""
    if migration_status is not None:
        rows = db.execute(
            text(f"SELECT {_SELECT_COLUMNS} FROM b2bi_inbound_flow WHERE migration_status = :status"),
            {"status": migration_status.upper()},
        ).mappings().all()
    else:
        rows = db.execute(
            text(f"SELECT {_SELECT_COLUMNS} FROM b2bi_inbound_flow")
        ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{inbound_flow_id}")
def get_inbound_flow(inbound_flow_id: int, db: Session = Depends(get_db)) -> dict:
    """Return a single inbound flow by id."""
    row = db.execute(
        text(f"SELECT {_SELECT_COLUMNS} FROM b2bi_inbound_flow WHERE inbound_flow_id = :id"),
        {"id": inbound_flow_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Inbound flow not found")
    return dict(row)


@router.get("/by-transfer/{transfer_id}")
def get_inbound_flow_by_transfer(transfer_id: int, db: Session = Depends(get_db)) -> dict:
    """Return the inbound flow row for a given transfer (transfer_id is unique on this table)."""
    row = db.execute(
        text(f"SELECT {_SELECT_COLUMNS} FROM b2bi_inbound_flow WHERE transfer_id = :id"),
        {"id": transfer_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="No inbound flow found for this transfer")
    return dict(row)


@router.patch("/{inbound_flow_id}/status")
def update_inbound_flow_status(
    inbound_flow_id: int, body: StatusIn, db: Session = Depends(get_db)
) -> dict:
    """Update an inbound flow's migration_status."""
    new_status = body.migration_status.upper()
    if new_status not in _VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid migration_status: {new_status}")

    result = db.execute(
        text(
            "UPDATE b2bi_inbound_flow SET migration_status = :status "
            "WHERE inbound_flow_id = :id"
        ),
        {"status": new_status, "id": inbound_flow_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Inbound flow not found")
    db.commit()
    return {"inbound_flow_id": inbound_flow_id, "migration_status": new_status}
