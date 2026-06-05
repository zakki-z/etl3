from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])

_AIRFLOW_BASE     = os.getenv("AIRFLOW_API_URL",  "http://localhost:8080/api/v2")
_AIRFLOW_AUTH_URL = os.getenv("AIRFLOW_AUTH_URL", "http://localhost:8080/auth/token")
_AIRFLOW_DAG_ID   = os.getenv("AIRFLOW_DAG_ID",   "cft_daily_import")
_AIRFLOW_USER     = os.getenv("AIRFLOW_API_USER",  "admin")

_AIRFLOW_PASS_FILE = Path.home() / "airflow" / "simple_auth_manager_passwords.json.generated"

# Sentinel dict returned when Airflow is not reachable / not configured.
_UNREACHABLE = {
    "state": "unreachable",
    "dag_run_id": None,
    "start_date": None,
    "end_date": None,
}


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


def _get_token() -> str | None:
    """Obtain a bearer token from Airflow 3 SimpleAuthManager.

    Returns None (instead of raising) when Airflow is not configured or
    not reachable, so callers can degrade gracefully.
    """
    password = _resolve_password()
    if not password:
        return None

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                _AIRFLOW_AUTH_URL,
                json={"username": _AIRFLOW_USER, "password": password},
            )
    except httpx.ConnectError:
        return None

    if resp.status_code != 200:
        return None

    data = resp.json()
    token = data.get("access_token") or data.get("token")
    return token or None


def _airflow_client(token: str) -> httpx.Client:
    return httpx.Client(
        base_url=_AIRFLOW_BASE,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )


@router.post("/trigger")
def trigger_pipeline() -> dict:
    token = _get_token()
    if token is None:
        return {
            "dag_run_id": None,
            "state": "unreachable",
            "logical_date": None,
            "error": "Airflow is not reachable or not configured (AIRFLOW_API_PASSWORD missing).",
        }

    try:
        with _airflow_client(token) as client:
            resp = client.post(
                f"/dags/{_AIRFLOW_DAG_ID}/dagRuns",
                json={"dag_run_id": None},
            )
            if resp.status_code not in (200, 201):
                return {
                    "dag_run_id": None,
                    "state": "error",
                    "logical_date": None,
                    "error": f"Airflow returned {resp.status_code}: {resp.text}",
                }
            data = resp.json()
        return {
            "dag_run_id": data.get("dag_run_id"),
            "state":      data.get("state"),
            "logical_date": data.get("logical_date"),
        }
    except httpx.ConnectError:
        return {
            "dag_run_id": None,
            "state": "unreachable",
            "logical_date": None,
            "error": "Airflow is not reachable.",
        }


@router.get("/status")
def pipeline_status() -> dict:
    token = _get_token()
    if token is None:
        return _UNREACHABLE

    try:
        with _airflow_client(token) as client:
            resp = client.get(
                f"/dags/{_AIRFLOW_DAG_ID}/dagRuns",
                params={"limit": 1, "order_by": "-startDate"},
            )
            if resp.status_code != 200:
                return _UNREACHABLE
            runs = resp.json().get("dag_runs", [])
    except httpx.ConnectError:
        return _UNREACHABLE

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