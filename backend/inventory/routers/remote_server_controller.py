"""
Remote Server Controller
────────────────────────
CRUD for remote CFT server connection profiles,
plus endpoints to trigger SSH data pull and test connections.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.engine import Connection
from sqlalchemy import select, text

from commons.database import get_db, engine
from ..models.remote_server import remote_server_table
from ..schemas.remote_server import (
    RemoteServerCreate,
    RemoteServerUpdate,
    RemoteServerResponse,
    RemoteServerPullRequest,
    RemoteServerPullResponse,
)

log = logging.getLogger("cft_extractor")

router = APIRouter(prefix="/api/v1/remote-servers", tags=["Remote Servers"])

LOCAL_CACHE_ROOT = "/opt/cft-data"


def _row_to_dict(row) -> dict:
    return dict(row._mapping)


def _default_local_dest(name: str) -> str:
    safe_name = name.strip().lower().replace(" ", "_")
    return f"{LOCAL_CACHE_ROOT}/{safe_name}"


def _build_extraction_summary(db_engine) -> dict:
    """Build a summary of what was extracted into the database."""
    summary = {}
    table_names = [
        "server", "cfttcp", "cftprot", "cftssl",
        "partner", "flow", "processing",
        "bosco_route", "copilot_activity", "migration",
    ]
    with db_engine.connect() as conn:
        for name in table_names:
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar()
                summary[name] = count
            except Exception:
                summary[name] = 0

        # Migration complexity breakdown
        try:
            cx_rows = conn.execute(
                text("SELECT complexity, COUNT(*) FROM migration GROUP BY complexity")
            ).fetchall()
            summary["migration_complexity"] = {r[0]: r[1] for r in cx_rows if r[0]}
        except Exception:
            summary["migration_complexity"] = {}

        # Dormant partners
        try:
            dormant = conn.execute(
                text("SELECT name FROM partner WHERE activity_status = 'DORMANT'")
            ).fetchall()
            summary["dormant_partners"] = [d[0] for d in dormant]
        except Exception:
            summary["dormant_partners"] = []

    return summary


#LIST
@router.get("", response_model=List[RemoteServerResponse])
def list_remote_servers(
    environment: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    conn: Connection = Depends(get_db),
):
    query = select(remote_server_table)
    if environment:
        query = query.where(remote_server_table.c.environment == environment.upper())
    if is_active is not None:
        query = query.where(remote_server_table.c.is_active == is_active)
    query = query.order_by(remote_server_table.c.name)
    query = query.offset((page - 1) * page_size).limit(page_size)
    rows = conn.execute(query).fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/{server_id}", response_model=RemoteServerResponse)
def get_remote_server(server_id: int, conn: Connection = Depends(get_db)):
    row = conn.execute(
        select(remote_server_table).where(remote_server_table.c.id == server_id)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Remote server {server_id} not found")
    return _row_to_dict(row)

@router.post("", response_model=RemoteServerResponse, status_code=201)
def create_remote_server(payload: RemoteServerCreate, conn: Connection = Depends(get_db)):
    existing = conn.execute(
        select(remote_server_table).where(remote_server_table.c.name == payload.name)
    ).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail=f"Remote server with name '{payload.name}' already exists")

    values = payload.model_dump()
    if not values.get("local_dest"):
        values["local_dest"] = _default_local_dest(values["name"])

    now = datetime.utcnow()
    values["created_at"] = now
    values["updated_at"] = now

    result = conn.execute(remote_server_table.insert().values(**values))
    server_id = result.inserted_primary_key[0]

    return _row_to_dict(
        conn.execute(select(remote_server_table).where(remote_server_table.c.id == server_id)).fetchone()
    )


@router.patch("/{server_id}", response_model=RemoteServerResponse)
def update_remote_server(server_id: int, payload: RemoteServerUpdate, conn: Connection = Depends(get_db)):
    row = conn.execute(
        select(remote_server_table).where(remote_server_table.c.id == server_id)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Remote server {server_id} not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data:
        conflict = conn.execute(
            select(remote_server_table).where(
                (remote_server_table.c.name == update_data["name"]) &
                (remote_server_table.c.id != server_id)
            )
        ).fetchone()
        if conflict:
            raise HTTPException(status_code=409, detail=f"Name '{update_data['name']}' already taken")

    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        conn.execute(
            remote_server_table.update()
            .where(remote_server_table.c.id == server_id)
            .values(**update_data)
        )

    return _row_to_dict(
        conn.execute(select(remote_server_table).where(remote_server_table.c.id == server_id)).fetchone()
    )


@router.delete("/{server_id}", status_code=204)
def delete_remote_server(server_id: int, conn: Connection = Depends(get_db)):
    row = conn.execute(
        select(remote_server_table).where(remote_server_table.c.id == server_id)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Remote server {server_id} not found")
    conn.execute(remote_server_table.delete().where(remote_server_table.c.id == server_id))
    return None


#PULL DATA
@router.post("/{server_id}/pull", response_model=RemoteServerPullResponse)
def pull_from_remote_server(
    server_id: int,
    payload: RemoteServerPullRequest = RemoteServerPullRequest(),
    conn: Connection = Depends(get_db),
):
    """
    Trigger an SSH/SCP data pull from a saved remote server profile.
    Optionally runs the full extraction pipeline afterwards.

    The SSH password must be provided in the request body for
    password-based authentication (it is never stored in the database).
    """
    row = conn.execute(
        select(remote_server_table).where(remote_server_table.c.id == server_id)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Remote server {server_id} not found")

    server = dict(row._mapping)
    local_dest = server["local_dest"] or _default_local_dest(server["name"])

    # Validate that password is provided when auth_method is password
    if server["auth_method"] == "password" and not payload.ssh_password:
        raise HTTPException(
            status_code=422,
            detail="SSH password is required for password-based authentication. "
                   "Please provide it in the request.",
        )

    from ..services.remote_data_pull import pull_data_via_ssh

    try:
        local_path = pull_data_via_ssh(
            remote_host=server["remote_host"],
            remote_user=server["remote_user"],
            remote_data_dir=server["remote_data_dir"],
            local_dest=local_dest,
            remote_port=server["remote_port"] or 22,
            ssh_key_path=server.get("ssh_key_path"),
            ssh_password=payload.ssh_password,
        )

        conn.execute(
            remote_server_table.update()
            .where(remote_server_table.c.id == server_id)
            .values(
                last_pull_at=datetime.utcnow(),
                last_pull_status="success",
                last_pull_message=f"Data pulled to {local_path}",
                updated_at=datetime.utcnow(),
            )
        )

        extraction_ran = False
        extraction_summary = None

        if payload.run_extraction:
            from services.extraction_orchestrator import run_extraction

            # Use the app's own database engine URL
            db_url = payload.db_url or str(engine.url)

            run_extraction(
                data_dir=str(local_path),
                db_url=db_url,
                reset=payload.reset,
            )
            extraction_ran = True

            # Build summary from the freshly populated database
            extraction_summary = _build_extraction_summary(engine)

        return RemoteServerPullResponse(
            server_id=server_id,
            server_name=server["name"],
            status="success",
            message=f"Data pulled successfully to {local_path}",
            local_path=str(local_path),
            extraction_ran=extraction_ran,
            extraction_summary=extraction_summary,
        )

    except Exception as e:
        log.exception(f"Pull failed for remote server {server['name']}")

        conn.execute(
            remote_server_table.update()
            .where(remote_server_table.c.id == server_id)
            .values(
                last_pull_at=datetime.utcnow(),
                last_pull_status="failed",
                last_pull_message=str(e)[:2000],
                updated_at=datetime.utcnow(),
            )
        )

        raise HTTPException(status_code=500, detail=str(e))


#TEST CONNECTION
@router.post("/{server_id}/test-connection")
def test_remote_connection(
    server_id: int,
    payload: RemoteServerPullRequest = RemoteServerPullRequest(),
    conn: Connection = Depends(get_db),
):
    """
    Test SSH connectivity to a remote server.
    Accepts an optional ssh_password in the body for password-based auth.
    """
    row = conn.execute(
        select(remote_server_table).where(remote_server_table.c.id == server_id)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Remote server {server_id} not found")

    server = dict(row._mapping)
    ssh_password = payload.ssh_password

    try:
        import paramiko

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": server["remote_host"],
            "port": server["remote_port"] or 22,
            "username": server["remote_user"],
            "timeout": 10,
        }

        if server["auth_method"] == "key" and server.get("ssh_key_path"):
            connect_kwargs["key_filename"] = server["ssh_key_path"]
        elif server["auth_method"] == "password" and ssh_password:
            connect_kwargs["password"] = ssh_password
        else:
            connect_kwargs["allow_agent"] = True
            connect_kwargs["look_for_keys"] = True

        ssh.connect(**connect_kwargs)

        sftp = ssh.open_sftp()
        try:
            sftp.stat(server["remote_data_dir"])
            dir_exists = True
            dir_message = f"Directory '{server['remote_data_dir']}' exists"
        except FileNotFoundError:
            dir_exists = False
            dir_message = f"Directory '{server['remote_data_dir']}' NOT found on remote"

        contents = []
        if dir_exists:
            try:
                contents = sftp.listdir(server["remote_data_dir"])
            except Exception:
                pass

        sftp.close()
        ssh.close()

        return {
            "status": "success",
            "message": f"SSH connection to {server['remote_host']} successful",
            "directory_exists": dir_exists,
            "directory_message": dir_message,
            "directory_contents": contents[:50],
        }

    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="paramiko is not installed. Install with: pip install paramiko",
        )
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Connection failed: {str(e)}",
            "directory_exists": None,
            "directory_message": None,
            "directory_contents": [],
        }