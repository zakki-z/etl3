import { API_BASE_URL } from '../config';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${path}`;
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json', ...options?.headers },
        ...options,
    });
    if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(body.detail || `HTTP ${res.status}`);
    }
    if (res.status === 204) return undefined as unknown as T;
    return res.json();
}

export const api = {
    get: <T>(path: string) => request<T>(path),
    post: <T>(path: string, body?: unknown) =>
        request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
    patch: <T>(path: string, body?: unknown) =>
        request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
    delete: (path: string) => request<void>(path, { method: 'DELETE' }),
};

// ── Phase 1 ───────────────────────────────────────────────────────────────

export async function fetchServers(): Promise<any[]> {
    return api.get('/api/v1/servers');
}
export async function fetchCFTPartners(): Promise<any[]> {
    return api.get('/api/v1/partners');
}
export async function fetchCFTFlows(): Promise<any[]> {
    return api.get('/api/v1/flows');
}
export async function fetchTransfers(): Promise<any[]> {
    return api.get('/api/v1/transfers');
}
export async function fetchPostProcessingScripts(): Promise<any[]> {
    return api.get('/api/v1/scripts');
}
export async function fetchCFTTCP(): Promise<any[]>             { return api.get('/api/v1/cft-tcp'); }
export async function fetchCFTWithoutPartner(): Promise<any[]>  { return api.get('/api/v1/stg-cft-tcp-without-partner'); }
export async function fetchFlowActions(): Promise<any[]>        { return api.get('/api/v1/flow-actions'); }
export async function fetchCFTConfig(): Promise<any[]>          { return api.get('/api/v1/moncft-configs'); }
export async function fetchBoscoSendConfig(): Promise<any[]>    { return api.get('/api/v1/boscosend-configs'); }

// ── B2Bi domain — per-row migration_status (no jobs/exceptions/mapping rules) ──

export interface Community {
    community_id: string;
    name: string;
    default_routing_id: string;
}

export async function fetchCommunities(): Promise<Community[]> {
    return api.get('/api/v1/communities');
}

export type MigrationStatus = 'DRAFT' | 'READY' | 'PUSHED' | 'VALIDATED' | 'MIGRATED' | 'ERROR';

export interface B2biPartner {
    b2bi_partner_id: number;
    partner_code: string;
    party_name: string;
    partner_contact: string | null;
    b2bi_party_remote_id: string | null;
    nrpart: string | null;
    ssl: number | null;
    migration_status: MigrationStatus;
    nspart: string | null;
    community_id: string;
}

export interface B2biPartnerDelivery {
    partner_delivery_id: number;
    friendly_name: string;
    b2bi_delivery_remote_id: string | null;
    host: string | null;
    port: string | null;
    parm: string | null;
    idf: string;
    nfname: string | null;
    data_encoding: string | null;
    record_format: string | null;
    record_length: string | null;
    fname: string | null;
    migration_status: MigrationStatus;
    b2bi_partner_id: number;
    transfer_id: number;
}

export interface B2biInboundFlow {
    inbound_flow_id: number;
    idf: string;
    fname: string | null;
    parm: string | null;
    nfname: string | null;
    rename_rule: string | null;
    migration_status: MigrationStatus;
    b2bi_partner_id: number;
    transfer_id: number;
}

export async function fetchB2biPartners(params?: {
    migration_status?: MigrationStatus;
    community_id?: string;
}): Promise<B2biPartner[]> {
    const qs = new URLSearchParams();
    if (params?.migration_status) qs.set('migration_status', params.migration_status);
    if (params?.community_id) qs.set('community_id', params.community_id);
    const query = qs.toString();
    return api.get(`/api/v1/b2bi-partners${query ? `?${query}` : ''}`);
}

export async function fetchB2biPartnerDeliveries(partnerId: number): Promise<B2biPartnerDelivery[]> {
    return api.get(`/api/v1/b2bi-partners/${partnerId}/deliveries`);
}

export async function fetchB2biInboundFlows(partnerId: number): Promise<B2biInboundFlow[]> {
    return api.get(`/api/v1/b2bi-partners/${partnerId}/inbound-flows`);
}

export async function updateB2biPartnerStatus(
    partnerId: number,
    migration_status: MigrationStatus,
): Promise<{ b2bi_partner_id: number; migration_status: MigrationStatus }> {
    return api.patch(`/api/v1/b2bi-partners/${partnerId}/status`, { migration_status });
}

export async function updateB2biDeliveryStatus(
    deliveryId: number,
    migration_status: MigrationStatus,
): Promise<{ partner_delivery_id: number; migration_status: MigrationStatus }> {
    return api.patch(`/api/v1/b2bi-partner-deliveries/${deliveryId}/status`, { migration_status });
}

export async function updateB2biInboundFlowStatus(
    flowId: number,
    migration_status: MigrationStatus,
): Promise<{ inbound_flow_id: number; migration_status: MigrationStatus }> {
    return api.patch(`/api/v1/b2bi-inbound-flows/${flowId}/status`, { migration_status });
}

// ── B2Bi generation (CFT → B2Bi) ────────────────────────────────────────────

export interface GenerationReport {
    community_id: string;
    partners_processed: number;
    partners_ready: number;
    partners_draft: number;
    partners_error: number;
    deliveries_created: number;
    deliveries_updated: number;
    inbound_flows_created: number;
    inbound_flows_updated: number;
    skipped_rows: number;
    errors: string[];
}

export async function triggerB2biGeneration(
    communityId: string,
    partnerIds?: string[],
): Promise<GenerationReport> {
    return api.post('/api/v1/b2bi-generation/trigger', {
        community_id: communityId,
        partner_ids: partnerIds ?? null,
    });
}
// ── SSH Pull ──────────────────────────────────────────────────────────────
// Append this block to the bottom of src/services/api.ts

export interface SshPullRequest {
    server_id: string;
    host: string;
    port: number;
    username: string;
    password: string;
    remote_conf_dir: string;
    environment: string;
}

export interface SshPullReport {
    server_id: string;
    host: string;
    files_pulled: number;
    filenames: string[];
    partner_parsed: number;
    partner_upserted: number;
    tcp_parsed: number;
    tcp_upserted: number;
    send_parsed: number;
    recv_parsed: number;
    flow_upserted: number;
    tcp_missing_partner: number;
    error: string | null;
}

export async function sshPull(body: SshPullRequest): Promise<SshPullReport> {
    return api.post('/api/v1/ssh-pull', body);
}