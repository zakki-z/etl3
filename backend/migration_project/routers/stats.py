from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("")
def get_stats(db: Session = Depends(get_db)) -> dict:
    """Return high-level inventory counts for the dashboard."""
    def count(query: str) -> int:
        return db.execute(text(query)).scalar() or 0

    return {
        "partners":             count("SELECT COUNT(*) FROM cft_partner"),
        "partners_ssl":         count("SELECT COUNT(*) FROM cft_partner WHERE `ssl` = 1"),
        "flows_send":           count("SELECT COUNT(*) FROM cft_flow WHERE direct = 'send'"),
        "flows_recv":           count("SELECT COUNT(*) FROM cft_flow WHERE direct = 'recv'"),
        "flows_xlate":          count("SELECT COUNT(*) FROM cft_flow WHERE xlate = 1"),
        "transfers_ok":         count("SELECT COUNT(*) FROM transfer WHERE statut = 'OK'"),
        "transfers_nok":        count("SELECT COUNT(*) FROM transfer WHERE statut = 'NOK'"),
        "servers":              count("SELECT COUNT(*) FROM server"),
        "scripts":              count("SELECT COUNT(*) FROM post_processing_scripts"),
        "tcp_without_partner":  count("SELECT COUNT(*) FROM stg_cft_tcp_without_partner"),
    }