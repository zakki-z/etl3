from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/communities", tags=["communities"])


@router.get("")
def list_communities(db: Session = Depends(get_db)) -> list[dict]:
    """Return all communities."""
    rows = db.execute(
        text("SELECT community_id, name, default_routing_id FROM community ORDER BY name")
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{community_id}")
def get_community(community_id: str, db: Session = Depends(get_db)) -> dict:
    """Return a single community by id."""
    row = db.execute(
        text("SELECT community_id, name, default_routing_id FROM community WHERE community_id = :id"),
        {"id": community_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Community not found")
    return dict(row)


@router.get("/{community_id}/routing-ids")
def list_community_routing_ids(community_id: str, db: Session = Depends(get_db)) -> list[dict]:
    """Return all routing ids attached to a community."""
    rows = db.execute(
        text(
            "SELECT routing_id, community_id FROM community_routing_ids "
            "WHERE community_id = :id ORDER BY routing_id"
        ),
        {"id": community_id},
    ).mappings().all()
    return [dict(r) for r in rows]


# ── Flat router for the standalone community_routing_ids table view ───────
routing_ids_router = APIRouter(prefix="/api/v1/community-routing-ids", tags=["communities"])


@routing_ids_router.get("")
def list_all_community_routing_ids(db: Session = Depends(get_db)) -> list[dict]:
    """Return every routing id across all communities (flat table view)."""
    rows = db.execute(
        text("SELECT routing_id, community_id FROM community_routing_ids ORDER BY community_id, routing_id")
    ).mappings().all()
    return [dict(r) for r in rows]