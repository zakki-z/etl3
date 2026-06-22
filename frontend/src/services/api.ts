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

// ── Phase 2 — Generation jobs ─────────────────────────────────────────────

export interface GenerationJob {
    id: number;
    status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
    started_at: string | null;
    finished_at: string | null;
    partners_total: number;
    partners_ok: number;
    partners_blocked: number;
    created_at: string;
}

export interface GenerationReport {
    job_id: number;
    partners_total: number;
    partners_ok: number;
    partners_blocked: number;
    configs_created: number;
    exceptions_logged: number;
}

export interface B2biConfig {
    id: number;
    job_id: number;
    partner_id: string;
    payload: Record<string, unknown>;
    sync_status: 'PENDING' | 'APPROVED' | 'DEPLOYED' | 'FAILED';
    generated_at: string;
    approved_at: string | null;
}

export interface ExceptionLog {
    id: number;
    job_id: number;
    partner_id: string;
    severity: 'BLOCKING' | 'WARNING';
    exception_type: string;
    message: string;
    resolved: boolean;
    resolved_at: string | null;
    resolution_note: string | null;
    created_at: string;
}

export interface ExceptionSummary {
    blocking_open: number;
    blocking_resolved: number;
    warning_open: number;
    warning_resolved: number;
}

export interface MappingRule {
    id: number;
    rule_name: string;
    source_field: string | null;
    target_field: string;
    transform_type: 'direct' | 'static' | 'lookup' | 'template';
    transform_params: Record<string, unknown> | null;
    is_active: boolean;
    created_at: string;
}

export async function triggerGeneration(): Promise<GenerationReport> {
    return api.post('/api/v1/generation-jobs');
}

export async function fetchGenerationJobs(): Promise<GenerationJob[]> {
    return api.get('/api/v1/generation-jobs');
}

export async function fetchJobConfigs(jobId: number, syncStatus?: string): Promise<B2biConfig[]> {
    const qs = syncStatus ? `?sync_status=${syncStatus}` : '';
    return api.get(`/api/v1/generation-jobs/${jobId}/configs${qs}`);
}

export async function approveConfig(jobId: number, configId: number): Promise<{ id: number; sync_status: string }> {
    return api.post(`/api/v1/generation-jobs/${jobId}/configs/${configId}/approve`);
}

// ── Phase 2 — Exceptions ──────────────────────────────────────────────────

export async function fetchExceptions(params: {
    job_id?: number;
    severity?: string;
    resolved?: boolean;
}): Promise<ExceptionLog[]> {
    const qs = new URLSearchParams();
    if (params.job_id !== undefined) qs.set('job_id', String(params.job_id));
    if (params.severity) qs.set('severity', params.severity);
    if (params.resolved !== undefined) qs.set('resolved', String(params.resolved));
    const query = qs.toString();
    return api.get(`/api/v1/exceptions${query ? `?${query}` : ''}`);
}

export async function fetchExceptionSummary(jobId: number): Promise<ExceptionSummary> {
    return api.get(`/api/v1/exceptions/jobs/${jobId}/summary`);
}

export async function resolveException(id: number, note?: string): Promise<{ id: number; resolved: boolean }> {
    return api.post(`/api/v1/exceptions/${id}/resolve`, { note: note ?? null });
}

// ── Phase 2 — Mapping rules ───────────────────────────────────────────────

export async function fetchMappingRules(): Promise<MappingRule[]> {
    return api.get('/api/v1/mapping-rules');
}

export async function toggleMappingRule(id: number): Promise<{ id: number; is_active: boolean }> {
    return api.patch(`/api/v1/mapping-rules/${id}/toggle`);
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