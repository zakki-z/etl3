from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/views", tags=["views"])


# ── v_cft_flow_xlate_enabled ──────────────────────────────────────────────

@router.get("/cft-flow-xlate-enabled")
def list_cft_flow_xlate_enabled(db: Session = Depends(get_db)) -> list[dict]:
    """Return all cft_flow rows with xlate enabled, via the read-only view."""
    rows = db.execute(
        text(
            "SELECT idf_code, direct, fcode, ftype, flrecl, frecfm, fname, xlate "
            "FROM v_cft_flow_xlate_enabled ORDER BY idf_code, direct"
        )
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/cft-flow-xlate-enabled/{idf_code}/{direct}")
def get_cft_flow_xlate_enabled(idf_code: str, direct: str, db: Session = Depends(get_db)) -> dict:
    """Return a single xlate-enabled flow by its composite key (idf_code, direct)."""
    row = db.execute(
        text(
            "SELECT idf_code, direct, fcode, ftype, flrecl, frecfm, fname, xlate "
            "FROM v_cft_flow_xlate_enabled WHERE idf_code = :idf_code AND direct = :direct"
        ),
        {"idf_code": idf_code, "direct": direct},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Xlate-enabled flow not found")
    return dict(row)


# ── v_cft_partner_ssl_enabled ─────────────────────────────────────────────

@router.get("/cft-partner-ssl-enabled")
def list_cft_partner_ssl_enabled(db: Session = Depends(get_db)) -> list[dict]:
    """Return all cft_partner rows with SSL enabled, via the read-only view."""
    rows = db.execute(
        text(
            "SELECT id, nspart, nrpart, `ssl`, sap, nspassw, nrpassw "
            "FROM v_cft_partner_ssl_enabled ORDER BY id"
        )
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/cft-partner-ssl-enabled/{partner_id}")
def get_cft_partner_ssl_enabled(partner_id: str, db: Session = Depends(get_db)) -> dict:
    """Return a single SSL-enabled partner by id."""
    row = db.execute(
        text(
            "SELECT id, nspart, nrpart, `ssl`, sap, nspassw, nrpassw "
            "FROM v_cft_partner_ssl_enabled WHERE id = :id"
        ),
        {"id": partner_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="SSL-enabled partner not found")
    return dict(row)
