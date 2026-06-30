from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db
from migration_project.services.b2bi_generation_service import (
    B2biGenerationService,
    GenerationReport,
)

router = APIRouter(prefix="/api/v1/b2bi-generation", tags=["b2bi-generation"])

_service = B2biGenerationService()


class TriggerGenerationIn(BaseModel):
    community_id: str
    # Optional: regenerate only these CFT partners (by cft_partner.id).
    # Omit to regenerate every CFT partner.
    partner_ids: list[str] | None = None


class GenerationReportOut(BaseModel):
    community_id: str
    partners_processed: int
    partners_ready: int
    partners_draft: int
    partners_error: int
    deliveries_created: int
    deliveries_updated: int
    inbound_flows_created: int
    inbound_flows_updated: int
    skipped_rows: int
    errors: list[str]

    @classmethod
    def from_report(cls, report: GenerationReport) -> "GenerationReportOut":
        return cls(**report.__dict__)


@router.post("/trigger", response_model=GenerationReportOut)
def trigger_generation(body: TriggerGenerationIn, db: Session = Depends(get_db)) -> GenerationReportOut:
    """Generate (or refresh) B2Bi Trading Partner config rows from the CFT
    inventory tables for the given target community.

    Idempotent: rows already advanced past DRAFT/ERROR (READY, PUSHED,
    VALIDATED, MIGRATED) are left untouched, so re-running this after a
    partner has been pushed/validated won't reset that progress.
    """
    try:
        report = _service.generate(db, body.community_id, body.partner_ids)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return GenerationReportOut.from_report(report)