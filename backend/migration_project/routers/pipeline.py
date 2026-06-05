from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])

_AIRFLOW_BASE     = os.getenv("AIRFLOW_API_URL",  "http://localhost:8080/api/v2")
_AIRFLOW_AUTH_URL = os.getenv("AIRFLOW_AUTH_URL", "http://localhost:8080/auth/token")
_AIRFLOW_DAG_ID   = os.getenv("AIRFLOW_DAG_ID",   "cft_daily_import")
_AIRFLOW_USER     = os.getenv("AIRFLOW_API_USER",  "admin")

# Password resolution order:
#   1. AIRFLOW_API_PASSWORD env var (set in .env)
#   2. Airflow's generated password file (standalone mode on Mac/Linux)
_AIRFLOW_PASS_FILE = Path.home() / "airflow" / "simple_auth_manager_passwords.json.generated"


def _resolve_password() -> str:
    explicit = os.getenv("AIRFLOW_API_PASSWORD", "").strip()
    if explicit:
        return explicit
    if _AIRFLOW_PASS_FILE.exists():
        try:
            data = json.loads(_AIRFLOW_PASS_FILE.read_text())
            return str(data.get(_AIRFLOW_USER, ""))
        except Exception:
            pass
    return ""


def _get_token() -> str:
    """Obtain a bearer token from Airflow 3 SimpleAuthManager."""
    password = _resolve_password()
    if not password:
        raise HTTPException(status_code=502, detail="Airflow password not configured")

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                _AIRFLOW_AUTH_URL,
                json={"username": _AIRFLOW_USER, "password": password},
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Airflow is not reachable")

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Airflow auth failed ({resp.status_code}): {resp.text}",
        )

    data = resp.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        raise HTTPException(status_code=502, detail="Airflow returned no token")
    return token


def _airflow_client(token: str) -> httpx.Client:
    return httpx.Client(
        base_url=_AIRFLOW_BASE,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )


@router.post("/trigger")
def trigger_pipeline() -> dict:
    try:
        token = _get_token()
        with _airflow_client(token) as client:
            resp = client.post(
                f"/dags/{_AIRFLOW_DAG_ID}/dagRuns",
                json={"dag_run_id": None},
            )
            if resp.status_code not in (200, 201):
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            data = resp.json()
        return {
            "dag_run_id": data.get("dag_run_id"),
            "state":       data.get("state"),
            "logical_date": data.get("logical_date"),
        }
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Airflow is not reachable")


@router.get("/status")
def pipeline_status() -> dict:
    try:
        token = _get_token()
        with _airflow_client(token) as client:
            resp = client.get(
                f"/dags/{_AIRFLOW_DAG_ID}/dagRuns",
                params={"limit": 1, "order_by": "-startDate"},
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            runs = resp.json().get("dag_runs", [])
    except httpx.ConnectError:
        return {
            "state": "unreachable",
            "dag_run_id": None,
            "start_date": None,
            "end_date": None,
        }

    if not runs:
        return {
            "state": "no_runs",
            "dag_run_id": None,
            "start_date": None,
            "end_date": None,
        }

    latest = runs[0]
    return {
        "dag_run_id": latest.get("dag_run_id"),
        "state":      latest.get("state"),
        "start_date": latest.get("start_date"),
        "end_date":   latest.get("end_date"),
    }