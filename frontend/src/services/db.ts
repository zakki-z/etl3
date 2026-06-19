/**
 * Database service — fetches live data from the backend API.
 *
 * Each "table" corresponds to a real backend endpoint + SQLAlchemy model.
 * The column definitions mirror the backend Pydantic response schemas
 * and are kept in sync with the actual `migration_db` MySQL schema.
 *
 * Endpoint reality check (backend/migration_project/routers/):
 *   servers.py          → /api/v1/servers
 *   partners.py         → /api/v1/partners
 *   flows.py            → /api/v1/flows
 *   transfers.py        → /api/v1/transfers
 *   scripts.py          → /api/v1/scripts
 *   stats.py            → /api/v1/stats
 *   pipeline.py         → /api/v1/pipeline
 *
 * Tables without a dedicated router yet (cft_tcp, flow_action, moncft_config,
 * boscosend_config, stg_cft_tcp_without_partner, b2bi_*, community, views)
 * have their endpoint marked with a TODO prefix so the UI can surface them
 * as "coming soon" rather than silently returning empty rows.
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
  /** Backend GET path. Paths starting with TODO: have no router yet. */
  endpoint: string;
  rows: Record<string, unknown>[];
}

// ── Table metadata matching backend models ───────────────────────────────

export const tableDefinitions: Omit<DatabaseTable, 'rows'>[] = [
  // ── Core CFT inventory ─────────────────────────────────────────────────
  {
    name: 'server',
    description: 'Profils de connexion serveurs distants (SSH)',
    endpoint: '/api/v1/servers',                    // ✅ servers.py
    columns: [
      { name: 'id',          type: 'string' },
      { name: 'host',        type: 'string' },
      { name: 'environment', type: 'string' },
    ],
  },
  {
    name: 'cft_partner',
    description: 'Partenaires CFT (CFTPART)',
    endpoint: '/api/v1/partners',                   // ✅ partners.py
    columns: [
      { name: 'id',              type: 'string'  },
      { name: 'nspart',          type: 'string'  },
      { name: 'nrpart',          type: 'string'  },
      { name: 'ssl',             type: 'boolean' },
      { name: 'sap',             type: 'string'  },
      { name: 'nspassw',         type: 'string'  },
      { name: 'nrpassw',         type: 'string'  },
      { name: 'ipart',           type: 'string'  },
      { name: 'partner_contact', type: 'string'  },
    ],
  },
  {
    name: 'cft_flow',
    description: 'Flux CFT (CFTSEND / CFTRECV)',
    endpoint: '/api/v1/flows',                      // ✅ flows.py
    columns: [
      { name: 'id',       type: 'int'     },
      { name: 'fcode',    type: 'string'  },
      { name: 'ftype',    type: 'string'  },
      { name: 'flrecl',   type: 'string'  },
      { name: 'frecfm',   type: 'string'  },
      { name: 'direct',   type: 'string'  },
      { name: 'fname',    type: 'string'  },
      { name: 'xlate',    type: 'boolean' },
      { name: 'idf_code', type: 'string'  },
      { name: 'exec',     type: 'string'  },
      { name: 'exece',    type: 'string'  },
    ],
  },
  {
    name: 'cft_tcp',
    description: 'Configuration réseau TCP par partenaire (CFTTCP)',
    endpoint: '/api/v1/cft-tcp',                    // ✅ cft_tcp.py
    columns: [
      { name: 'partner_id', type: 'string' },
      { name: 'cnxout',     type: 'string' },
      { name: 'host',       type: 'string' },
    ],
  },
  {
    name: 'transfer',
    description: 'Transferts CFT (lien partenaire ↔ flux)',
    endpoint: '/api/v1/transfers',                  // ✅ transfers.py
    columns: [
      { name: 'id',         type: 'int'    },
      { name: 'partner_id', type: 'string' },
      { name: 'idf_id',     type: 'int'    },
      { name: 'date',       type: 'date'   },
      { name: 'direct',     type: 'string' },
      { name: 'server_id',  type: 'string' },
      { name: 'statut',     type: 'string' },   // enum: OK | NOK
    ],
  },
  {
    name: 'flow_action',
    description: 'Actions associées aux flux (lien vers scripts)',
    // Scripts router exposes actions under /scripts/{id}/actions only.
    // A flat list endpoint does not exist yet.
    endpoint: '/api/v1/flow-actions',               // ✅ flow_actions.py
    columns: [
      { name: 'id',           type: 'int'    },
      { name: 'script_id',    type: 'int'    },
      { name: 'scope_type',   type: 'string' },   // enum: GLOBAL | IDF | PART | IPART | IDF_SCRIPT
      { name: 'idf_id',       type: 'int'    },
      { name: 'partner_id',   type: 'string' },
      { name: 'ipart_value',  type: 'string' },
      { name: 'action_order', type: 'int'    },
      { name: 'action_text',  type: 'string' },
    ],
  },
  {
    name: 'post_processing_scripts',
    description: 'Scripts de post-traitement',
    endpoint: '/api/v1/scripts',                    // ✅ scripts.py
    columns: [
      { name: 'id',          type: 'int'    },
      { name: 'server_id',   type: 'string' },
      { name: 'script_path', type: 'string' },
      { name: 'script_name', type: 'string' },
    ],
  },
  {
    name: 'moncft_config',
    description: 'Configuration MonCFT (monitoring)',
    endpoint: '/api/v1/moncft-configs',             // ✅ moncft_configs.py
    columns: [
      { name: 'id',          type: 'int'    },
      { name: 'fname',       type: 'string' },
      { name: 'filtre',      type: 'string' },
      { name: 'parm',        type: 'string' },
      { name: 'nfname',      type: 'string' },
      { name: 'transfer_id', type: 'int'    },
      { name: 'SAPPL',       type: 'string' },
      { name: 'RAPPL',       type: 'string' },
      { name: 'SUSER',       type: 'string' },
    ],
  },
  {
    name: 'boscosend_config',
    description: 'Configuration BoscoSend',
    endpoint: '/api/v1/boscosend-configs',          // ✅ boscosend_configs.py
    columns: [
      { name: 'id',               type: 'int'    },
      { name: 'remote_address',   type: 'string' },
      { name: 'remote_subdir',    type: 'string' },
      { name: 'transfer_id',      type: 'int'    },
      { name: 'localdir',         type: 'string' },
      { name: 'backup_dir',       type: 'string' },
      { name: 'file_search_mask', type: 'string' },
      { name: 'nom_section',      type: 'string' },
      { name: 'Cmdb-Prestation',  type: 'string' },
    ],
  },
  {
    name: 'stg_cft_tcp_without_partner',
    description: 'TCP entries sans partenaire associé (staging)',
    endpoint: '/api/v1/stg-cft-tcp-without-partner', // ✅ stg_cft_tcp.py
    columns: [
      { name: 'id',     type: 'string' },
      { name: 'cnxout', type: 'string' },
      { name: 'host',   type: 'string' },
      { name: 'reason', type: 'string' },
    ],
  },

  // ── B2Bi generation targets ────────────────────────────────────────────
  {
    name: 'b2bi_partner',
    description: 'Partenaires B2Bi générés (Trading Partners)',
    endpoint: 'TODO:/api/v1/b2bi-partners',         // ❌ Phase 2 — no router yet
    columns: [
      { name: 'b2bi_partner_id',      type: 'int'     },
      { name: 'partner_code',         type: 'string'  },
      { name: 'party_name',           type: 'string'  },
      { name: 'partner_contact',      type: 'string'  },
      { name: 'b2bi_party_remote_id', type: 'string'  },
      { name: 'nrpart',               type: 'string'  },
      { name: 'ssl',                  type: 'boolean' },
      { name: 'migration_status',     type: 'string'  },
      { name: 'nspart',               type: 'string'  },
      { name: 'community_id',         type: 'string'  },
    ],
  },
  {
    name: 'b2bi_partner_delivery',
    description: 'Canaux de livraison B2Bi (delivery channels)',
    endpoint: 'TODO:/api/v1/b2bi-partner-deliveries', // ❌ Phase 2 — no router yet
    columns: [
      { name: 'partner_delivery_id',     type: 'int'    },
      { name: 'friendly_name',           type: 'string' },
      { name: 'b2bi_delivery_remote_id', type: 'string' },
      { name: 'host',                    type: 'string' },
      { name: 'port',                    type: 'string' },
      { name: 'parm',                    type: 'string' },
      { name: 'idf',                     type: 'string' },
      { name: 'nfname',                  type: 'string' },
      { name: 'data_encoding',           type: 'string' },
      { name: 'record_format',           type: 'string' },
      { name: 'record_length',           type: 'string' },
      { name: 'fname',                   type: 'string' },
      { name: 'migration_status',        type: 'string' },
      { name: 'b2bi_partner_id',         type: 'int'    },
      { name: 'transfer_id',             type: 'int'    },
    ],
  },
  {
    name: 'b2bi_inbound_flow',
    description: 'Flux entrants B2Bi (inbound flows)',
    endpoint: 'TODO:/api/v1/b2bi-inbound-flows',    // ❌ Phase 2 — no router yet
    columns: [
      { name: 'inbound_flow_id',  type: 'int'    },
      { name: 'idf',              type: 'string' },
      { name: 'fname',            type: 'string' },
      { name: 'parm',             type: 'string' },
      { name: 'nfname',           type: 'string' },
      { name: 'rename_rule',      type: 'string' },
      { name: 'migration_status', type: 'string' },
      { name: 'b2bi_partner_id',  type: 'int'    },
      { name: 'transfer_id',      type: 'int'    },
    ],
  },

  // ── Community (B2Bi routing) ───────────────────────────────────────────
  {
    name: 'community',
    description: 'Communautés B2Bi (routing communities)',
    endpoint: 'TODO:/api/v1/communities',           // ❌ Phase 2 — no router yet
    columns: [
      { name: 'community_id',       type: 'string' },
      { name: 'name',               type: 'string' },
      { name: 'default_routing_id', type: 'string' },
    ],
  },
  {
    name: 'community_routing_ids',
    description: 'Identifiants de routage par communauté',
    endpoint: 'TODO:/api/v1/community-routing-ids', // ❌ Phase 2 — no router yet
    columns: [
      { name: 'routing_id',   type: 'string' },
      { name: 'community_id', type: 'string' },
    ],
  },

  // ── Views (read-only) ──────────────────────────────────────────────────
  {
    name: 'v_cft_flow_xlate_enabled',
    description: 'Vue — flux CFT avec translation activée',
    endpoint: 'TODO:/api/v1/views/cft-flow-xlate-enabled', // ❌ no router yet
    columns: [
      { name: 'idf_code', type: 'string'  },
      { name: 'direct',   type: 'string'  },
      { name: 'fcode',    type: 'string'  },
      { name: 'ftype',    type: 'string'  },
      { name: 'flrecl',   type: 'string'  },
      { name: 'frecfm',   type: 'string'  },
      { name: 'fname',    type: 'string'  },
      { name: 'xlate',    type: 'boolean' },
    ],
  },
  {
    name: 'v_cft_partner_ssl_enabled',
    description: 'Vue — partenaires CFT avec SSL activé',
    endpoint: 'TODO:/api/v1/views/cft-partner-ssl-enabled', // ❌ no router yet
    columns: [
      { name: 'id',      type: 'string'  },
      { name: 'nspart',  type: 'string'  },
      { name: 'nrpart',  type: 'string'  },
      { name: 'ssl',     type: 'boolean' },
      { name: 'sap',     type: 'string'  },
      { name: 'nspassw', type: 'string'  },
      { name: 'nrpassw', type: 'string'  },
    ],
  },
];

// ── Fetch helpers ────────────────────────────────────────────────────────

/**
 * Returns true for tables whose backend router hasn't been built yet.
 * The UI can use this to show a "coming soon" badge instead of an empty table.
 */
export function isEndpointMissing(endpoint: string): boolean {
  return endpoint.startsWith('TODO:');
}

/**
 * Fetch rows for a table from the backend.
 * Uses the endpoint defined in tableDefinitions directly — no second lookup map.
 * Returns [] for tables whose endpoint is not implemented yet (TODO: prefix).
 */
export async function fetchTableRows(
    tableName: string,
    servers: { id: number }[] = [],
): Promise<Record<string, unknown>[]> {
  const def = tableDefinitions.find((t) => t.name === tableName);
  if (!def) return [];

  // Not yet implemented — avoid a 404 that would fill the console with noise.
  if (isEndpointMissing(def.endpoint)) return [];

  // Tables that need per-server fetching (server-scoped sub-resources).
  const serverScopedTables: Record<string, (serverId: number) => string> = {
    cfttcp:      (id) => `/api/v1/servers/${id}/cfttcp`,
    cftprot:     (id) => `/api/v1/servers/${id}/cftprot`,
    cftssl:      (id) => `/api/v1/servers/${id}/cftssl`,
    processing:  (id) => `/api/v1/servers/${id}/processing`,
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

  // All other tables: use the endpoint from the definition directly.
  try {
    return await api.get<Record<string, unknown>[]>(`${def.endpoint}?page_size=200`);
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
