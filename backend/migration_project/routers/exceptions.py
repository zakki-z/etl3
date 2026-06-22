from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.repositories.exception_log_repository import ExceptionLogRepository
from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/exceptions", tags=["exceptions"])

_repo = ExceptionLogRepository()


class ResolveIn(BaseModel):
    note: str | None = None


@router.get("")
def list_exceptions(
    job_id: int | None = Query(None, description="Filter by generation job"),
    partner_id: str | None = Query(None, description="Filter by partner"),
    severity: str | None = Query(None, description="BLOCKING or WARNING"),
    resolved: bool | None = Query(None, description="Filter by resolved status"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return exception log entries with optional filters."""
    conditions: list[str] = []
    params: dict = {}

    if job_id is not None:
        conditions.append("job_id = :job_id")
        params["job_id"] = job_id
    if partner_id is not None:
        conditions.append("partner_id = :partner_id")
        params["partner_id"] = partner_id
    if severity is not None:
        conditions.append("severity = :severity")
        params["severity"] = severity.upper()
    if resolved is not None:
        conditions.append("resolved = :resolved")
        params["resolved"] = 1 if resolved else 0

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = db.execute(
        text(f"""
            SELECT id, job_id, partner_id, severity, exception_type,
                   message, resolved, resolved_at, resolution_note, created_at
            FROM exception_log
            {where}
            ORDER BY severity DESC, id
        """),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{exception_id}")
def get_exception(exception_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.execute(
        text("""
            SELECT id, job_id, partner_id, severity, exception_type,
                   message, resolved, resolved_at, resolution_note, created_at
            FROM exception_log WHERE id = :id
        """),
        {"id": exception_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Exception not found")
    return dict(row)


@router.post("/{exception_id}/resolve")
def resolve_exception(
    exception_id: int,
    body: ResolveIn,
    db: Session = Depends(get_db),
) -> dict:
    """
    Mark a single exception as resolved with an optional note.
    Resolving all BLOCKING exceptions for a partner unblocks its config for approval.
    """
    ok = _repo.resolve(db, exception_id, note=body.note)
    if not ok:
        raise HTTPException(status_code=404, detail="Exception not found")
    db.commit()
    return {"id": exception_id, "resolved": True}


@router.get("/jobs/{job_id}/summary")
def exception_summary(job_id: int, db: Session = Depends(get_db)) -> dict:
    """Return blocking/warning counts for a job, split by resolved status."""
    row = db.execute(
        text("""
            SELECT
                SUM(severity = 'BLOCKING' AND resolved = 0)  AS blocking_open,
                SUM(severity = 'BLOCKING' AND resolved = 1)  AS blocking_resolved,
                SUM(severity = 'WARNING'  AND resolved = 0)  AS warning_open,
                SUM(severity = 'WARNING'  AND resolved = 1)  AS warning_resolved
            FROM exception_log
            WHERE job_id = :job_id
        """),
        {"job_id": job_id},
    ).mappings().first()
    return dict(row) if row else {}
