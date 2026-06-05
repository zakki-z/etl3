from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])

# Airflow API base — override via env var if needed.
_AIRFLOW_BASE = os.getenv("AIRFLOW_API_URL", "http://localhost:8080/api/v1")
_AIRFLOW_DAG_ID = os.getenv("AIRFLOW_DAG_ID", "cft_daily_import")
_AIRFLOW_USER = os.getenv("AIRFLOW_API_USER", "admin")
_AIRFLOW_PASS = os.getenv("AIRFLOW_API_PASSWORD", "")


def _airflow_client() -> httpx.Client:
    return httpx.Client(
        base_url=_AIRFLOW_BASE,
        auth=(_AIRFLOW_USER, _AIRFLOW_PASS),
        timeout=10,
    )


@router.post("/trigger")
def trigger_pipeline() -> dict:
    """Trigger the cft_daily_import DAG manually."""
    with _airflow_client() as client:
        resp = client.post(f"/dags/{_AIRFLOW_DAG_ID}/dagRuns", json={})
        if resp.status_code not in (200, 200):
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        data = resp.json()
    return {
        "dag_run_id": data.get("dag_run_id"),
        "state": data.get("state"),
        "logical_date": data.get("logical_date"),
    }


@router.get("/status")
def pipeline_status() -> dict:
    """Return the latest DAG run state."""
    with _airflow_client() as client:
        resp = client.get(
            f"/dags/{_AIRFLOW_DAG_ID}/dagRuns",
            params={"limit": 1, "order_by": "-start_date"},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        runs = resp.json().get("dag_runs", [])

    if not runs:
        return {"state": "no_runs", "dag_run_id": None, "start_date": None}

    latest = runs[0]
    return {
        "dag_run_id": latest.get("dag_run_id"),
        "state": latest.get("state"),
        "start_date": latest.get("start_date"),
        "end_date": latest.get("end_date"),
    }
