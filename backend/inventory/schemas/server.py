from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from datetime import datetime

# Server
class ServerBase(BaseModel):
    name: str
    ip_address: Optional[str] = None
    environment: str = "PROD"
    install_path: Optional[str] = None
    os_info: Optional[str] = None
    comment: Optional[str] = None


class ServerCreate(ServerBase):
    pass


class ServerUpdate(BaseModel):
    ip_address: Optional[str] = None
    environment: Optional[str] = None
    install_path: Optional[str] = None
    os_info: Optional[str] = None
    comment: Optional[str] = None


class ServerResponse(ServerBase):
    id: int
    raw_export_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# CFTTCP-
class CftTcpBase(BaseModel):
    name: str
    host: Optional[str] = None
    port: Optional[int] = None
    cnx_in: Optional[int] = None
    cnx_out: Optional[int] = None
    cnx_inout: Optional[int] = None
    retry_wait: Optional[int] = None
    retry_max: Optional[int] = None
    ssl_id: Optional[str] = None
    comment: Optional[str] = None


class CftTcpResponse(CftTcpBase):
    id: int
    server_id: int
    raw_config: Optional[str] = None

    class Config:
        from_attributes = True

# CFTPROT
class CftProtBase(BaseModel):
    name: str
    prot_type: Optional[str] = None
    net: Optional[str] = None
    sap: Optional[str] = None
    ssl_id: Optional[str] = None
    compress: Optional[str] = None
    restart: Optional[str] = None
    concat: Optional[str] = None
    comment: Optional[str] = None


class CftProtResponse(CftProtBase):
    id: int
    server_id: int
    raw_config: Optional[str] = None

    class Config:
        from_attributes = True


# CFTSSL
class CftSslBase(BaseModel):
    name: str
    direct: Optional[str] = None
    rootcid: Optional[str] = None
    usercid: Optional[str] = None
    userkey: Optional[str] = None
    version: Optional[str] = None
    verify: Optional[str] = None
    ciphlist: Optional[str] = None


class CftSslResponse(CftSslBase):
    id: int
    server_id: int
    raw_config: Optional[str] = None

    class Config:
        from_attributes = True


# Partner
class PartnerBase(BaseModel):
    name: str
    nrpart: Optional[str] = None
    nspart: Optional[str] = None
    prot: Optional[str] = None
    sap: Optional[str] = None
    state: Optional[str] = None
    commut: Optional[str] = None
    idf_list: Optional[str] = None
    cfttcp_name: Optional[str] = None
    comment: Optional[str] = None


class PartnerResponse(PartnerBase):
    id: int
    server_id: int
    cfttcp_id: Optional[int] = None
    is_active: Optional[bool] = None
    last_transfer_date: Optional[datetime] = None
    transfer_count_12m: Optional[int] = None
    avg_daily_volume: Optional[float] = None
    activity_status: Optional[str] = None
    raw_config: Optional[str] = None

    class Config:
        from_attributes = True

# Flow
class FlowBase(BaseModel):
    idf: str
    cft_type: str
    ftype: Optional[str] = None
    fcode: Optional[str] = None
    fname: Optional[str] = None
    wfname: Optional[str] = None
    nfname: Optional[str] = None
    exec_: Optional[str] = Field(None, alias="exec")
    comment: Optional[str] = None
    partner_list: Optional[str] = None


class FlowResponse(FlowBase):
    id: int
    partner_id: int
    server_id: int
    is_active: Optional[bool] = None
    last_transfer_date: Optional[datetime] = None
    transfer_count_12m: Optional[int] = None
    avg_daily_volume: Optional[float] = None
    activity_status: Optional[str] = None
    raw_config: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


# Processing (Exit Scripts)
class ProcessingResponse(BaseModel):
    id: int
    flow_id: Optional[int] = None
    server_id: int
    script_path: Optional[str] = None
    script_type: Optional[str] = None
    bucket: Optional[str] = None
    classification_notes: Optional[str] = None
    migration_action: Optional[str] = None
    calls_unknown_scripts: bool = False
    unknown_script_paths: Optional[str] = None
    branch_condition: Optional[str] = None
    branch_action: Optional[str] = None
    branch_has_unknown_call: bool = False

    class Config:
        from_attributes = True


# Bosco Route
class BoscoRouteResponse(BaseModel):
    id: int
    server_id: int
    section_name: Optional[str] = None
    route_type: Optional[str] = None
    active: Optional[bool] = None
    local_dir: Optional[str] = None
    backup_dir: Optional[str] = None
    dest_dir: Optional[str] = None
    archive_dir: Optional[str] = None
    remote_address: Optional[str] = None
    remote_port: Optional[int] = None
    remote_subdir: Optional[str] = None
    file_mask: Optional[str] = None
    protocol: Optional[str] = None
    partner_ref: Optional[str] = None
    idf_ref: Optional[str] = None
    schedule: Optional[str] = None
    processing_app: Optional[str] = None
    comment: Optional[str] = None

    class Config:
        from_attributes = True


# Copilot Activity
class CopilotActivityResponse(BaseModel):
    id: int
    server_name: Optional[str] = None
    partner_id_ref: Optional[str] = None
    idf: Optional[str] = None
    direction: Optional[str] = None
    last_transfer_date: Optional[datetime] = None
    transfer_count_12m: Optional[int] = None
    avg_daily_volume: Optional[float] = None
    status_recommendation: Optional[str] = None

    class Config:
        from_attributes = True


# Migration
class MigrationBase(BaseModel):
    status: Optional[str] = "pending"
    complexity: Optional[str] = "low"
    notes: Optional[str] = None


class MigrationUpdate(BaseModel):
    status: Optional[str] = None
    complexity: Optional[str] = None
    notes: Optional[str] = None


class MigrationResponse(MigrationBase):
    id: int
    flow_id: int
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True


# Extraction
class ExtractionRequest(BaseModel):
    data_dir: str
    db_url: str
    reset: bool = False


class ExtractionSummary(BaseModel):
    servers: int = 0
    cfttcp: int = 0
    cftprot: int = 0
    cftssl: int = 0
    partners: int = 0
    flows: int = 0
    processing: int = 0
    bosco_routes: int = 0
    copilot_activities: int = 0
    migrations: int = 0
    migration_complexity: Dict[str, int] = {}
    dormant_partners: List[str] = []


class RemotePullRequest(BaseModel):
    remote_host: str
    remote_user: str
    remote_data_dir: str
    local_dest: str
    remote_port: int = 22
    ssh_key_path: Optional[str] = None
    ssh_password: Optional[str] = None


# Pagination
class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int