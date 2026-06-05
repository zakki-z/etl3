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
    patch: <T>(path: string, body: unknown) =>
        request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
    delete: (path: string) => request<void>(path, { method: 'DELETE' }),
};

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
export async function fetchCFTTCP(): Promise<any[]>             { return []; }
export async function fetchCFTWithoutPartner(): Promise<any[]> { return []; }
export async function fetchFlowActions(): Promise<any[]>        { return []; }
export async function fetchCFTConfig(): Promise<any[]>          { return []; }
export async function fetchBoscoSendConfig(): Promise<any[]>    { return []; }