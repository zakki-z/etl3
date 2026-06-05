"""
Flow Controller
───────────────
CRUD operations for CFT flows (CFTSEND / CFTRECV), with
server-scoped and partner-scoped listing.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.engine import Connection
from sqlalchemy import select

from commons.database import get_db
from ..models.flow import flow_table
from ..schemas import FlowResponse

router = APIRouter(prefix="/api/v1", tags=["Flows"])


#LIST by server
@router.get(
    "/servers/{server_id}/flows",
    response_model=List[FlowResponse],
)
def list_flows_by_server(
    server_id: int,
    cft_type: Optional[str] = Query(None, description="SEND or RECV"),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_db),
):
    """List all flows belonging to a server."""
    query = select(flow_table).where(flow_table.c.server_id == server_id)

    if cft_type:
        query = query.where(flow_table.c.cft_type == cft_type.upper())
    if is_active is not None:
        query = query.where(flow_table.c.is_active == is_active)

    query = query.order_by(flow_table.c.idf)
    query = query.offset((page - 1) * page_size).limit(page_size)

    rows = conn.execute(query).fetchall()
    return [dict(r._mapping) for r in rows]


#LIST by partner ──────────────────────────────────────────────────────────
@router.get(
    "/partners/{partner_id}/flows",
    response_model=List[FlowResponse],
)
def list_flows_by_partner(
    partner_id: int,
    cft_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_db),
):
    """List all flows for a specific partner."""
    query = select(flow_table).where(flow_table.c.partner_id == partner_id)

    if cft_type:
        query = query.where(flow_table.c.cft_type == cft_type.upper())

    query = query.order_by(flow_table.c.idf)
    query = query.offset((page - 1) * page_size).limit(page_size)

    rows = conn.execute(query).fetchall()
    return [dict(r._mapping) for r in rows]


#GLOBAL LIST ──────────────────────────────────────────────────────────────
@router.get("/flows", response_model=List[FlowResponse])
def list_all_flows(
    cft_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    idf: Optional[str] = Query(None, description="Filter by IDF identifier"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_db),
):
    """List flows across all servers with optional filters."""
    query = select(flow_table)

    if cft_type:
        query = query.where(flow_table.c.cft_type == cft_type.upper())
    if is_active is not None:
        query = query.where(flow_table.c.is_active == is_active)
    if idf:
        query = query.where(flow_table.c.idf.ilike(f"%{idf}%"))

    query = query.order_by(flow_table.c.server_id, flow_table.c.idf)
    query = query.offset((page - 1) * page_size).limit(page_size)

    rows = conn.execute(query).fetchall()
    return [dict(r._mapping) for r in rows]


#GET ──────────────────────────────────────────────────────────────────────
@router.get("/flows/{flow_id}", response_model=FlowResponse)
def get_flow(
    flow_id: int,
    conn: Connection = Depends(get_db),
):
    """Retrieve a single flow by ID."""
    row = conn.execute(
        select(flow_table).where(flow_table.c.id == flow_id)
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")

    return dict(row._mapping)