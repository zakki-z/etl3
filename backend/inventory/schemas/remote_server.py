from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Remote Server
class RemoteServerCreate(BaseModel):
    """Payload to register a new remote CFT server."""
    name: str = Field(..., min_length=1, max_length=100, description="Unique friendly name, e.g. CFT_PROD1")
    remote_host: str = Field(..., min_length=1, max_length=255, description="IP address or hostname")
    remote_port: int = Field(22, ge=1, le=65535)
    remote_user: str = Field(..., min_length=1, max_length=100)
    remote_data_dir: str = Field(..., min_length=1, max_length=1000, description="Absolute path on the remote server where CFT data resides")
    local_dest: Optional[str] = Field(None, max_length=1000, description="Local directory to cache pulled data. Auto-generated if omitted.")
    auth_method: str = Field("key", pattern="^(key|password|agent)$", description="Authentication method: key, password, or agent")
    ssh_key_path: Optional[str] = Field(None, max_length=1000, description="Path to SSH private key (required if auth_method=key)")
    environment: Optional[str] = Field(None, pattern="^(PROD|DMZ|RECETTE)$")
    description: Optional[str] = None
    is_active: bool = True


class RemoteServerUpdate(BaseModel):
    """Partial update payload for an existing remote server."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    remote_host: Optional[str] = Field(None, min_length=1, max_length=255)
    remote_port: Optional[int] = Field(None, ge=1, le=65535)
    remote_user: Optional[str] = Field(None, min_length=1, max_length=100)
    remote_data_dir: Optional[str] = Field(None, min_length=1, max_length=1000)
    local_dest: Optional[str] = Field(None, max_length=1000)
    auth_method: Optional[str] = Field(None, pattern="^(key|password|agent)$")
    ssh_key_path: Optional[str] = Field(None, max_length=1000)
    environment: Optional[str] = Field(None, pattern="^(PROD|DMZ|RECETTE)$")
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RemoteServerResponse(BaseModel):
    """Response model — never exposes passwords."""
    id: int
    name: str
    remote_host: str
    remote_port: int
    remote_user: str
    remote_data_dir: str
    local_dest: Optional[str] = None
    auth_method: str
    ssh_key_path: Optional[str] = None
    environment: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    last_pull_at: Optional[datetime] = None
    last_pull_status: Optional[str] = None
    last_pull_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RemoteServerPullRequest(BaseModel):
    """Optional overrides when triggering a pull from a saved server."""
    ssh_password: Optional[str] = Field(None, description="Password for this pull (not stored)")
    reset: bool = Field(False, description="If true, drop and recreate tables before extraction")
    run_extraction: bool = Field(True, description="If true, run the full extraction pipeline after pulling data")
    db_url: Optional[str] = Field(None, description="Override the database URL for extraction")


class RemoteServerPullResponse(BaseModel):
    """Result after triggering a pull, including extraction summary."""
    server_id: int
    server_name: str
    status: str              # success / failed
    message: str
    local_path: Optional[str] = None
    extraction_ran: bool = False
    extraction_summary: Optional[Dict[str, Any]] = Field(
        None,
        description="Summary of extracted records by table, plus migration complexity and dormant partners",
    )