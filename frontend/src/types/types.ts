export interface Server {
    id: number;
    name: string;
    remote_host: string;
    remote_port: number;
    remote_user: string;
    remote_data_dir: string;
    local_dest: string;
    auth_method: string;
    environment: string;
    is_active: boolean;
    last_pull_at: string;
    last_pull_status: string;
}

export interface CftPartner {
    id: string;
    nspart: string;
    nrpart: string;
    ssl: boolean;
    sap: string;
    nspassw: string;
    nrpassw: string;
}

export interface CftFlow {
    idf_code: string;
    direct: string;
    fcode: string;
    ftype: string;
    flrecl: string;
    frecfm: string;
    fname: string;
    xlate: boolean;
}

export interface CftTcp {
    partner_id: string;
    cnxout: string;
    host: string;
}

export interface Transfer {
    id: number;
    partner_id: string;
    idf_id: string;
    date: string;
    nbre_ligne: number;
    direct: string;
    is_migrable: boolean;
}

export interface FlowAction {
    id: number;
    transfer_id: number;
    script_id: number;
}

export interface PostProcessingScript {
    id: number;
    script_path: string;
    script_type: string;
}

export interface MoncftConfig {
    id: number;
    fname: string;
    filtre: string;
    parm: string;
    nfname: string;
    transfer_id: number;
    SAPPL: string;
    RAPPL: string;
    SUSER: string;
}

export interface BoscoSendConfig {
    id: number;
    remote_address: string;
    remote_subdir: string;
    transfer_id: number;
    localdir: string;
}

export interface CftTcpWithoutPartner {
    id: string;
    cnxout: string;
    host: string;
    reason: string;
}