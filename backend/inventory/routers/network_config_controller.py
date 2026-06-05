"""
Read-only endpoints for CFTTCP, CFTPROT, and CFTSSL records.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.engine import Connection
from sqlalchemy import select

from commons.database import get_db
from ..models.cfttcp import cfttcp_table
from ..models.cftprot import cftprot_table
from ..models.cftssl import cftssl_table
from ..schemas import CftTcpResponse, CftProtResponse, CftSslResponse

router = APIRouter(prefix="/api/v1", tags=["Network Config"])


#CFTTCP
@router.get(
    "/servers/{server_id}/cfttcp",
    response_model=List[CftTcpResponse],
)
def list_cfttcp_by_server(
    server_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_db),
):
    """List CFTTCP records for a server."""
    query = (
        select(cfttcp_table)
        .where(cfttcp_table.c.server_id == server_id)
        .order_by(cfttcp_table.c.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = conn.execute(query).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/cfttcp/{record_id}", response_model=CftTcpResponse)
def get_cfttcp(record_id: int, conn: Connection = Depends(get_db)):
    """Retrieve a single CFTTCP record."""
    row = conn.execute(
        select(cfttcp_table).where(cfttcp_table.c.id == record_id)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"CFTTCP {record_id} not found")
    return dict(row._mapping)


# ── CFTPROT
@router.get(
    "/servers/{server_id}/cftprot",
    response_model=List[CftProtResponse],
)
def list_cftprot_by_server(
    server_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_db),
):
    """List CFTPROT records for a server."""
    query = (
        select(cftprot_table)
        .where(cftprot_table.c.server_id == server_id)
        .order_by(cftprot_table.c.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = conn.execute(query).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/cftprot/{record_id}", response_model=CftProtResponse)
def get_cftprot(record_id: int, conn: Connection = Depends(get_db)):
    """Retrieve a single CFTPROT record."""
    row = conn.execute(
        select(cftprot_table).where(cftprot_table.c.id == record_id)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"CFTPROT {record_id} not found")
    return dict(row._mapping)


# ── CFTSSL ────────────────────────────────────────────────────────────────────
@router.get(
    "/servers/{server_id}/cftssl",
    response_model=List[CftSslResponse],
)
def list_cftssl_by_server(
    server_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_db),
):
    """List CFTSSL records for a server."""
    query = (
        select(cftssl_table)
        .where(cftssl_table.c.server_id == server_id)
        .order_by(cftssl_table.c.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = conn.execute(query).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/cftssl/{record_id}", response_model=CftSslResponse)
def get_cftssl(record_id: int, conn: Connection = Depends(get_db)):
    """Retrieve a single CFTSSL record."""
    row = conn.execute(
        select(cftssl_table).where(cftssl_table.c.id == record_id)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"CFTSSL {record_id} not found")
    return dict(row._mapping)