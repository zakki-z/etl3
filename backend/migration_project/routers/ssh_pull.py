from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from migration_project.services.ssh_pull_service import run_ssh_pull

router = APIRouter(prefix="/api/v1/ssh-pull", tags=["ssh-pull"])


class SshPullRequest(BaseModel):
    server_id: str = Field(..., description="Short identifier used as folder name, e.g. 'prod1'")
    host: str = Field(..., description="SSH hostname or IP")
    port: int = Field(22, description="SSH port")
    username: str
    password: str
    remote_conf_dir: str = Field(
        ...,
        description="Absolute path to the directory containing conf_cft.*.txt on the remote server",
    )
    environment: str = Field("production", description="Environment label stored in the server table")


class SshPullResponse(BaseModel):
    server_id: str
    host: str
    files_pulled: int
    filenames: list[str]
    partner_parsed: int
    partner_upserted: int
    tcp_parsed: int
    tcp_upserted: int
    send_parsed: int
    recv_parsed: int
    flow_upserted: int
    tcp_missing_partner: int
    error: str | None


@router.post("", response_model=SshPullResponse)
def ssh_pull(body: SshPullRequest) -> SshPullResponse:
    """
    SSH into a CFT server, download conf_cft.*.txt files,
    and run the full import pipeline.

    Credentials are used once and never persisted.
    Returns a detailed import report, or an error message on failure.
    """
    try:
        report = run_ssh_pull(
            server_id=body.server_id,
            host=body.host,
            port=body.port,
            username=body.username,
            password=body.password,
            remote_conf_dir=body.remote_conf_dir,
            environment=body.environment,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    return SshPullResponse(
        server_id=report.server_id,
        host=report.host,
        files_pulled=report.files_pulled,
        filenames=report.filenames,
        partner_parsed=report.partner_parsed,
        partner_upserted=report.partner_upserted,
        tcp_parsed=report.tcp_parsed,
        tcp_upserted=report.tcp_upserted,
        send_parsed=report.send_parsed,
        recv_parsed=report.recv_parsed,
        flow_upserted=report.flow_upserted,
        tcp_missing_partner=report.tcp_missing_partner,
        error=report.error,
    )