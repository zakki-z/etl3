"""
CRUD operations for CFT partners, scoped to a server.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.engine import Connection
from sqlalchemy import select

from commons.database import get_db
from ..models.server import server_table
from ..models.partner import partner_table
from ..schemas import PartnerResponse

router = APIRouter(prefix="/api/v1", tags=["Partners"])


def _assert_server_exists(conn: Connection, server_id: int):
    row = conn.execute(
        select(server_table).where(server_table.c.id == server_id)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")


#LIST (server-scoped)
@router.get(
    "/servers/{server_id}/partners",
    response_model=List[PartnerResponse],
)
def list_partners_by_server(
    server_id: int,
    is_active: Optional[bool] = Query(None, description="Filter by activity status"),
    activity_status: Optional[str] = Query(None, description="ACTIVE, ACTIVE_LOW, DORMANT"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_db),
):
    """List all partners for a given server."""
    _assert_server_exists(conn, server_id)

    query = select(partner_table).where(partner_table.c.server_id == server_id)

    if is_active is not None:
        query = query.where(partner_table.c.is_active == is_active)
    if activity_status:
        query = query.where(partner_table.c.activity_status == activity_status.upper())

    query = query.order_by(partner_table.c.name)
    query = query.offset((page - 1) * page_size).limit(page_size)

    rows = conn.execute(query).fetchall()
    return [dict(r._mapping) for r in rows]


#GLOBAL LIST
@router.get("/partners", response_model=List[PartnerResponse])
def list_all_partners(
    is_active: Optional[bool] = Query(None),
    activity_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search partner name (case-insensitive)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_db),
):
    """List partners across all servers with optional filters."""
    query = select(partner_table)

    if is_active is not None:
        query = query.where(partner_table.c.is_active == is_active)
    if activity_status:
        query = query.where(partner_table.c.activity_status == activity_status.upper())
    if search:
        query = query.where(partner_table.c.name.ilike(f"%{search}%"))

    query = query.order_by(partner_table.c.server_id, partner_table.c.name)
    query = query.offset((page - 1) * page_size).limit(page_size)

    rows = conn.execute(query).fetchall()
    return [dict(r._mapping) for r in rows]


#GET
@router.get("/partners/{partner_id}", response_model=PartnerResponse)
def get_partner(
    partner_id: int,
    conn: Connection = Depends(get_db),
):
    """Retrieve a single partner by ID."""
    row = conn.execute(
        select(partner_table).where(partner_table.c.id == partner_id)
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Partner {partner_id} not found")

    return dict(row._mapping)