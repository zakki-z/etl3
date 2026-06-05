from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/servers", tags=["servers"])


@router.get("")
def list_servers(db: Session = Depends(get_db)) -> list[dict]:
    """Return all CFT servers."""
    rows = db.execute(text("SELECT id, host, environment FROM server")).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{server_id}")
def get_server(server_id: str, db: Session = Depends(get_db)) -> dict:
    """Return a single server by id."""
    row = db.execute(
        text("SELECT id, host, environment FROM server WHERE id = :id"),
        {"id": server_id},
    ).mappings().first()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Server not found")
    return dict(row)
