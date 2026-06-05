from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.engine import Connection
from sqlalchemy import select

from commons.database import get_db
from ..models.bosco_route import bosco_route_table
from ..schemas import BoscoRouteResponse

router = APIRouter(prefix="/api/v1", tags=["Bosco Routes"])


#LIST by server
@router.get(
    "/servers/{server_id}/bosco-routes",
    response_model=List[BoscoRouteResponse],
)
def list_bosco_routes_by_server(
    server_id: int,
    route_type: Optional[str] = Query(None, description="BOSCO_SEND or BOSCO_RECV"),
    active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_db),
):
    """List Bosco routes for a server."""
    query = select(bosco_route_table).where(bosco_route_table.c.server_id == server_id)

    if route_type:
        query = query.where(bosco_route_table.c.route_type == route_type.upper())
    if active is not None:
        query = query.where(bosco_route_table.c.active == active)

    query = query.order_by(bosco_route_table.c.section_name)
    query = query.offset((page - 1) * page_size).limit(page_size)

    rows = conn.execute(query).fetchall()
    return [dict(r._mapping) for r in rows]

@router.get("/bosco-routes/{route_id}", response_model=BoscoRouteResponse)
def get_bosco_route(
    route_id: int,
    conn: Connection = Depends(get_db),
):
    """Retrieve a single Bosco route by ID."""
    row = conn.execute(
        select(bosco_route_table).where(bosco_route_table.c.id == route_id)
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Bosco route {route_id} not found")

    return dict(row._mapping)