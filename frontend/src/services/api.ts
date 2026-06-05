import { IPublicClientApplication } from "@azure/msal-browser";
import {API_BASE_URL, loginRequest} from "../auth/authConfig";
import {MoncftConfig, Server, CftTcp, CftTcpWithoutPartner, CftFlow,
    CftPartner, FlowAction, BoscoSendConfig, Transfer,
    PostProcessingScript} from "../types/types";

async function getAccessToken(instance: IPublicClientApplication): Promise<string> {
    let account = instance.getActiveAccount();

    if (!account) {
        const accounts = instance.getAllAccounts();
        account = accounts[0];

        if (account) {
            instance.setActiveAccount(account);
        }
    }

    if (!account) {
        throw new Error("No active account");
    }

    const response = await instance.acquireTokenSilent({
        ...loginRequest,
        account,
    });

    return response.accessToken;
}
//
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

    // 204 No Content
    if (res.status === 204) return undefined as unknown as T;
    return res.json();
}
export const api = {
    get: <T>(path: string) => request<T>(path),

    post: <T>(path: string, body?: unknown) =>
        request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),

    patch: <T>(path: string, body: unknown) =>
        request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),

    delete: (path: string) =>
        request<void>(path, { method: 'DELETE' }),
};
//remote server
export async function fetchServers(instance: IPublicClientApplication): Promise<Server[]> {
    const token = await getAccessToken(instance);
    const res = await fetch(`${API_BASE_URL}/api/servers/`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}
//CFT
export async function fetchCFTConfig(instance: IPublicClientApplication): Promise<MoncftConfig[]> {
    const token = await getAccessToken(instance);
    const res = await fetch(`${API_BASE_URL}/api/cft/`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}
export async function fetchCFTFlows(instance: IPublicClientApplication): Promise<CftFlow[]> {
    const token = await getAccessToken(instance);
    const res = await fetch(`${API_BASE_URL}/api/cft/cft_flow`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}
export async function fetchCFTPartners(instance: IPublicClientApplication): Promise<CftPartner[]> {
    const token = await getAccessToken(instance);
    const res = await fetch(`${API_BASE_URL}/api/cft/cft_partner`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}
export async function fetchCFTTCP(instance: IPublicClientApplication): Promise<CftTcp[]> {
    const token = await getAccessToken(instance);
    const res = await fetch(`${API_BASE_URL}/api/cft/cft_tcp`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}
export async function fetchCFTWithoutPartner(instance: IPublicClientApplication): Promise<CftTcpWithoutPartner[]> {
    const token = await getAccessToken(instance);
    const res = await fetch(`${API_BASE_URL}/api/cft/cft_without_partner`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

export async function fetchPostProcessingScripts(instance: IPublicClientApplication): Promise<PostProcessingScript[]> {
    const token = await getAccessToken(instance);
    const res = await fetch(`${API_BASE_URL}/api/cft/cft_scripts`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}
//rest
export async function fetchFlowActions(instance: IPublicClientApplication): Promise<FlowAction[]> {
    const token = await getAccessToken(instance);
    const res = await fetch(`${API_BASE_URL}/api/rest/flow_actions`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}
export async function fetchTransfers(instance: IPublicClientApplication): Promise<Transfer[]> {
    const token = await getAccessToken(instance);
    const res = await fetch(`${API_BASE_URL}/api/rest/transfers`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}
export async function fetchBoscoSendConfig(instance: IPublicClientApplication): Promise<BoscoSendConfig[]> {
    const token = await getAccessToken(instance);
    const res = await fetch(`${API_BASE_URL}/api/rest/bosco_config`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}




