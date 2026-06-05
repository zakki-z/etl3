/**
 * Database service — fetches live data from the backend API.
 *
 * Each "table" corresponds to a real backend endpoint + SQLAlchemy model.
 * The column definitions mirror the backend Pydantic response schemas.
 */
import { api } from './api';

export interface TableColumn {
  name: string;
  type: string;
}

export interface DatabaseTable {
  name: string;
  description: string;
  columns: TableColumn[];
  endpoint: string;                       // backend GET path
  rows: Record<string, unknown>[];
}

// ── Table metadata matching backend models ───────────────────────────────

export const tableDefinitions: Omit<DatabaseTable, 'rows'>[] = [
  {
    name: 'server',
    description: 'Profils de connexion serveurs distants (SSH)',
    endpoint: '/api/v1/remote-servers',
    columns: [
      { name: 'id', type: 'string' },
      { name: 'host', type: 'string' },
      { name: 'environment', type: 'string' },
    ],
  },
  {
    name: 'cft_partner',
    description: 'Partenaires CFT (CFTPART)',
    endpoint: '/api/v1/cft-partners',
    columns: [
      { name: 'id', type: 'string' },
      { name: 'nspart', type: 'string' },
      { name: 'nrpart', type: 'string' },
      { name: 'ssl', type: 'boolean' },
      { name: 'sap', type: 'string' },
      { name: 'nspassw', type: 'string' },
      { name: 'nrpassw', type: 'string' },
      { name: 'ipart', type: 'string' },
    ],
  },
  {
    name: 'cft_flow',
    description: 'Flux CFT (CFTSEND / CFTRECV)',
    endpoint: '/api/v1/cft-flows',
    columns: [
      { name: 'id', type: 'int' },
      { name: 'fcode', type: 'string' },
      { name: 'ftype', type: 'string' },
      { name: 'flrecl', type: 'string' },
      { name: 'frecfm', type: 'string' },
      { name: 'direct', type: 'string' },
      { name: 'fname', type: 'string' },
      { name: 'xlate', type: 'boolean' },
      { name: 'idf_code', type: 'string' },
      { name: 'exec', type: 'string' },
      { name: 'exece', type: 'string' },
    ],
  },
  {
    name: 'cft_tcp',
    description: 'Configuration réseau TCP par partenaire (CFTTCP)',
    endpoint: '/api/v1/cft-tcp',
    columns: [
      { name: 'partner_id', type: 'string' },
      { name: 'cnxout', type: 'string' },
      { name: 'host', type: 'string' },
    ],
  },
  {
    name: 'transfer',
    description: 'Transferts CFT (lien partenaire ↔ flux)',
    endpoint: '/api/v1/transfers',
    columns: [
      { name: 'id', type: 'int' },
      { name: 'partner_id', type: 'string' },
      { name: 'idf_id', type: 'int' },
      { name: 'date', type: 'datetime' },
      { name: 'direct', type: 'string' },
      { name: 'is_migrable', type: 'boolean' },
      { name: 'server_id', type: 'string' },
      { name: 'statut', type: 'string' },
    ],
  },
  {
    name: 'flow_action',
    description: 'Actions associées aux flux (lien vers scripts)',
    endpoint: '/api/v1/flow-actions',
    columns: [
      { name: 'id', type: 'int' },
      { name: 'script_id', type: 'int' },
      { name: 'scope_type', type: 'string' },
      { name: 'idf_id', type: 'int' },
      { name: 'partner_id', type: 'string' },
      { name: 'ipart_value', type: 'string' },
      { name: 'action_order', type: 'int' },
      { name: 'action_text', type: 'string' },
    ],
  },
  {
    name: 'post_processing_scripts',
    description: 'Scripts de post-traitement',
    endpoint: '/api/v1/post-processing-scripts',
    columns: [
      { name: 'id', type: 'int' },
      { name: 'server_id', type: 'string' },
      { name: 'script_path', type: 'string' },
      { name: 'script_name', type: 'string' },
    ],
  },
  {
    name: 'moncft_config',
    description: 'Configuration MonCFT (monitoring)',
    endpoint: '/api/v1/moncft-configs',
    columns: [
      { name: 'id', type: 'int' },
      { name: 'fname', type: 'string' },
      { name: 'filtre', type: 'string' },
      { name: 'parm', type: 'string' },
      { name: 'nfname', type: 'string' },
      { name: 'transfer_id', type: 'int' },
      { name: 'SAPPL', type: 'string' },
      { name: 'RAPPL', type: 'string' },
      { name: 'SUSER', type: 'string' },
    ],
  },
  {
    name: 'boscosend_config',
    description: 'Configuration BoscoSend',
    endpoint: '/api/v1/boscosend-configs',
    columns: [
      { name: 'id', type: 'int' },
      { name: 'remote_address', type: 'string' },
      { name: 'remote_subdir', type: 'string' },
      { name: 'transfer_id', type: 'int' },
      { name: 'localdir', type: 'string' },
      { name: 'backup_dir', type: 'string' },
      { name: 'file_search_mask', type: 'string' },
      { name: 'nom_section', type: 'string' },
      { name: 'Cmdb-Prestation', type: 'string' },
    ],
  },
  {
    name: 'cft_tcp_without_partner',
    description: 'TCP entries sans partenaire associé (staging)',
    endpoint: '/api/v1/stg-cft-tcp-without-partner',
    columns: [
      { name: 'id', type: 'string' },
      { name: 'cnxout', type: 'string' },
      { name: 'host', type: 'string' },
      { name: 'reason', type: 'string' },
    ],
  },
];

// ── Fetch helpers ────────────────────────────────────────────────────────

/**
 * Fetch rows for a table from the backend.
 * For server-scoped tables we aggregate across all known servers.
 */
export async function fetchTableRows(
    tableName: string,
    servers: { id: number }[] = [],
): Promise<Record<string, unknown>[]> {
  const def = tableDefinitions.find((t) => t.name === tableName);
  if (!def) return [];

  // Tables that need per-server fetching
  const serverScopedTables: Record<string, (serverId: number) => string> = {
    cfttcp: (id) => `/api/v1/servers/${id}/cfttcp`,
    cftprot: (id) => `/api/v1/servers/${id}/cftprot`,
    cftssl: (id) => `/api/v1/servers/${id}/cftssl`,
    processing: (id) => `/api/v1/servers/${id}/processing`,
    bosco_route: (id) => `/api/v1/servers/${id}/bosco-routes`,
  };

  if (serverScopedTables[tableName]) {
    const builder = serverScopedTables[tableName];
    const allRows: Record<string, unknown>[] = [];
    for (const srv of servers) {
      try {
        const rows = await api.get<Record<string, unknown>[]>(
            `${builder(srv.id)}?page_size=200`,
        );
        allRows.push(...rows);
      } catch {
        // server may not have this data — skip
      }
    }
    return allRows;
  }

  // Global endpoints — respect each controller's page_size limit
  const globalEndpoints: Record<string, string> = {
    server: '/api/v1/servers?page_size=100',
    partner: '/api/v1/partners?page_size=200',
    flow: '/api/v1/flows?page_size=200',
    copilot_activity: '/api/v1/copilot-activities?page_size=200',
    migration: '/api/v1/migrations?page_size=200',
    remote_server: '/api/v1/remote-servers?page_size=100',
  };

  const endpoint = globalEndpoints[tableName];
  if (!endpoint) return [];

  try {
    return await api.get<Record<string, unknown>[]>(endpoint);
  } catch {
    return [];
  }
}

export const databaseService = {
  async listTables(): Promise<DatabaseTable[]> {
    return tableDefinitions.map((def) => ({ ...def, rows: [] }));
  },

  async getTableWithData(
      name: string,
      servers: { id: number }[] = [],
  ): Promise<DatabaseTable | undefined> {
    const def = tableDefinitions.find((t) => t.name === name);
    if (!def) return undefined;
    const rows = await fetchTableRows(name, servers);
    return { ...def, rows };
  },
};
// ── Summary stats ────────────────────────────────────────────────────────

export interface InventoryStats {
  partners: number;
  partners_ssl: number;
  flows_send: number;
  flows_recv: number;
  flows_xlate: number;
  transfers_ok: number;
  transfers_nok: number;
  servers: number;
  scripts: number;
  tcp_without_partner: number;
}

export async function fetchStats(): Promise<InventoryStats | null> {
  try {
    return await api.get<InventoryStats>('/api/v1/stats');
  } catch {
    return null;
  }
}

// ── Pipeline control ─────────────────────────────────────────────────────

export interface PipelineStatus {
  dag_run_id: string | null;
  state: string;
  start_date: string | null;
  end_date: string | null;
}

export async function fetchPipelineStatus(): Promise<PipelineStatus | null> {
  try {
    return await api.get<PipelineStatus>('/api/v1/pipeline/status');
  } catch {
    return null;
  }
}

export async function triggerPipeline(): Promise<{ dag_run_id: string; state: string } | null> {
  try {
    return await api.post('/api/v1/pipeline/trigger', {});
  } catch {
    return null;
  }
}