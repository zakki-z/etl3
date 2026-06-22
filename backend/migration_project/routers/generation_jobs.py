from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.db import session_scope
from migration_project.repositories.b2bi_config_repository import B2biConfigRepository
from migration_project.repositories.generation_job_repository import GenerationJobRepository
from migration_project.routers.deps import get_db
from migration_project.services.generation_service import GenerationService

router = APIRouter(prefix="/api/v1/generation-jobs", tags=["generation-jobs"])

_job_repo = GenerationJobRepository()
_config_repo = B2biConfigRepository()


@router.post("", status_code=201)
def trigger_generation() -> dict:
    """
    Trigger a full Phase 2 generation run.
    Runs synchronously and returns the job summary on completion.
    """
    service = GenerationService()
    with session_scope() as session:
        report = service.run(session)
    return {
        "job_id": report.job_id,
        "partners_total": report.partners_total,
        "partners_ok": report.partners_ok,
        "partners_blocked": report.partners_blocked,
        "configs_created": report.configs_created,
        "exceptions_logged": report.exceptions_logged,
    }


@router.get("")
def list_jobs(db: Session = Depends(get_db)) -> list[dict]:
    """Return the 50 most recent generation jobs."""
    rows = db.execute(
        text("""
            SELECT id, status, started_at, finished_at,
                   partners_total, partners_ok, partners_blocked, created_at
            FROM generation_job ORDER BY id DESC LIMIT 50
        """)
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)) -> dict:
    """Return a single generation job with counts."""
    row = db.execute(
        text("""
            SELECT id, status, started_at, finished_at,
                   partners_total, partners_ok, partners_blocked, created_at
            FROM generation_job WHERE id = :id
        """),
        {"id": job_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return dict(row)


@router.get("/{job_id}/configs")
def list_job_configs(
    job_id: int,
    sync_status: str | None = Query(None, description="Filter by sync_status"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return all B2Bi configs produced by a generation job."""
    conditions = ["bc.job_id = :job_id"]
    params: dict = {"job_id": job_id}

    if sync_status:
        conditions.append("bc.sync_status = :sync_status")
        params["sync_status"] = sync_status.upper()

    where = "WHERE " + " AND ".join(conditions)
    rows = db.execute(
        text(f"""
            SELECT bc.id, bc.job_id, bc.partner_id, bc.sync_status,
                   bc.generated_at, bc.approved_at
            FROM b2bi_config bc
            {where}
            ORDER BY bc.partner_id
        """),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{job_id}/configs/{config_id}")
def get_job_config(job_id: int, config_id: int, db: Session = Depends(get_db)) -> dict:
    """Return a single B2Bi config including the full payload."""
    row = db.execute(
        text("""
            SELECT id, job_id, partner_id, payload, sync_status, generated_at, approved_at
            FROM b2bi_config
            WHERE id = :id AND job_id = :job_id
        """),
        {"id": config_id, "job_id": job_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Config not found")
    return dict(row)


@router.post("/{job_id}/configs/{config_id}/approve")
def approve_config(job_id: int, config_id: int, db: Session = Depends(get_db)) -> dict:
    """Mark a generated B2Bi config as approved (ready for Phase 3 deployment)."""
    ok = _config_repo.approve(db, config_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Config not found")
    db.commit()
    return {"id": config_id, "sync_status": "APPROVED"}
