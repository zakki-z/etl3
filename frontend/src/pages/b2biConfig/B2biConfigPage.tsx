import { useState, useEffect, useCallback, useRef } from 'react';
import { API_BASE_URL } from '../../config';
import './B2biConfigPage.css';

// ── Types ─────────────────────────────────────────────────────────────────────

type JobStatus = 'pending' | 'running' | 'completed' | 'failed';
type SyncStatus = 'draft' | 'approved' | 'pushed' | 'error';
type ExceptionType =
    | 'BUCKET_C_SCRIPT'
    | 'UNMAPPED_FIELD'
    | 'NO_TCP_CONFIG'
    | 'NO_ACTIVE_FLOWS'
    | 'INVALID_HOST'
    | 'MISSING_IDF'
    | 'MULTIPLE_PROTOCOLS'
    | 'UNKNOWN_SCRIPT_CALL';

interface GenerationJob {
    id: number;
    job_name: string;
    status: JobStatus;
    total_partners: number;
    processed: number;
    succeeded: number;
    failed: number;
    created_at: string;
    updated_at: string;
}

interface ExceptionLog {
    id: number;
    job_id: number;
    partner_id: string;
    exception_type: ExceptionType;
    field_name: string | null;
    resolved: boolean;
    created_at: string;
}

interface B2biConfig {
    migration_id: string;
    b2bi_partner_name: string;
    community_name: string;
    sync_status: SyncStatus;
    created_at: string;
}

interface InventoryStats {
    total_partners: number;
    ready_partners: number;
    blocked_partners: number;
}

// ── API helpers ───────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE_URL}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(body.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

const BLOCKING_EXCEPTIONS: ExceptionType[] = ['BUCKET_C_SCRIPT'];

function isBlocking(type: ExceptionType) {
    return BLOCKING_EXCEPTIONS.includes(type);
}

// ── Sub-components ────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: JobStatus | SyncStatus }) {
    const map: Record<string, string> = {
        pending:   'badge badge--pending',
        running:   'badge badge--running',
        completed: 'badge badge--ok',
        failed:    'badge badge--error',
        draft:     'badge badge--pending',
        approved:  'badge badge--ok',
        pushed:    'badge badge--pushed',
        error:     'badge badge--error',
    };
    const labels: Record<string, string> = {
        pending:   'En attente',
        running:   'En cours',
        completed: 'Terminé',
        failed:    'Échoué',
        draft:     'Brouillon',
        approved:  'Approuvé',
        pushed:    'Déployé',
        error:     'Erreur',
    };
    return <span className={map[status] ?? 'badge badge--pending'}>{labels[status] ?? status}</span>;
}

function ExceptionBadge({ type }: { type: ExceptionType }) {
    const blocking = isBlocking(type);
    return (
        <span className={`exc-badge ${blocking ? 'exc-badge--blocking' : 'exc-badge--warning'}`}>
            {blocking ? '⛔ ' : '⚠ '}{type.replace(/_/g, ' ')}
        </span>
    );
}

function ProgressBar({ value, total, status }: { value: number; total: number; status: JobStatus }) {
    const pct = total > 0 ? Math.round((value / total) * 100) : 0;
    return (
        <div className="progress-wrap">
            <div className={`progress-track`}>
                <div
                    className={`progress-fill progress-fill--${status}`}
                    style={{ width: `${pct}%` }}
                />
            </div>
            <span className="progress-label">{pct}%</span>
        </div>
    );
}

function formatDate(iso: string | null) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('fr-FR', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    });
}

// ── Main component ────────────────────────────────────────────────────────────

export default function B2biConfigPage() {
    const [jobs, setJobs] = useState<GenerationJob[]>([]);
    const [selectedJob, setSelectedJob] = useState<GenerationJob | null>(null);
    const [exceptions, setExceptions] = useState<ExceptionLog[]>([]);
    const [configs, setConfigs] = useState<B2biConfig[]>([]);
    const [inventoryStats, setInventoryStats] = useState<InventoryStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [triggering, setTriggering] = useState(false);
    const [triggerMsg, setTriggerMsg] = useState<{ text: string; ok: boolean } | null>(null);
    const [excFilter, setExcFilter] = useState<'all' | 'blocking' | 'unresolved'>('all');
    const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const loadJobs = useCallback(async () => {
        try {
            const data = await apiFetch<GenerationJob[]>('/api/v2/generation/jobs');
            setJobs(data);
            if (data.length > 0 && !selectedJob) {
                setSelectedJob(data[0]);
            }
        } catch {
            // silently fail — backend may not be on v2 yet
        }
    }, [selectedJob]);

    const loadInventoryStats = useCallback(async () => {
        try {
            const data = await apiFetch<InventoryStats>('/api/v2/inventory/stats');
            setInventoryStats(data);
        } catch {
            // Phase 2 backend not yet connected
        }
    }, []);

    const loadConfigs = useCallback(async () => {
        try {
            const data = await apiFetch<B2biConfig[]>('/api/v2/generation/configs');
            setConfigs(data);
        } catch {
            // silently fail
        }
    }, []);

    const loadExceptions = useCallback(async (jobId: number) => {
        try {
            const data = await apiFetch<ExceptionLog[]>(`/api/v2/generation/jobs/${jobId}/exceptions`);
            setExceptions(data);
        } catch {
            setExceptions([]);
        }
    }, []);

    // Initial load
    useEffect(() => {
        setLoading(true);
        Promise.all([loadJobs(), loadInventoryStats(), loadConfigs()]).finally(() =>
            setLoading(false),
        );
    }, [loadJobs, loadInventoryStats, loadConfigs]);

    // Load exceptions when job changes
    useEffect(() => {
        if (selectedJob) loadExceptions(selectedJob.id);
    }, [selectedJob, loadExceptions]);

    // Poll while a job is running
    useEffect(() => {
        const hasRunning = jobs.some((j) => j.status === 'running' || j.status === 'pending');
        if (hasRunning && !pollingRef.current) {
            pollingRef.current = setInterval(() => {
                loadJobs();
                loadConfigs();
                if (selectedJob) loadExceptions(selectedJob.id);
            }, 4000);
        } else if (!hasRunning && pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
        }
        return () => {
            if (pollingRef.current) clearInterval(pollingRef.current);
        };
    }, [jobs, selectedJob, loadJobs, loadConfigs, loadExceptions]);

    const handleTrigger = async () => {
        setTriggering(true);
        setTriggerMsg(null);
        try {
            const job = await apiFetch<GenerationJob>('/api/v2/generation/jobs', {
                method: 'POST',
                body: JSON.stringify({ job_name: `run_${new Date().toISOString().slice(0, 19)}` }),
            });
            setJobs((prev) => [job, ...prev]);
            setSelectedJob(job);
            setTriggerMsg({ text: `Job « ${job.job_name} » démarré.`, ok: true });
        } catch (e: any) {
            setTriggerMsg({ text: e.message || 'Échec du déclenchement.', ok: false });
        } finally {
            setTriggering(false);
        }
    };

    const filteredExceptions = exceptions.filter((e) => {
        if (excFilter === 'blocking') return isBlocking(e.exception_type);
        if (excFilter === 'unresolved') return !e.resolved;
        return true;
    });

    const blockingCount = exceptions.filter((e) => isBlocking(e.exception_type)).length;
    const unresolvedCount = exceptions.filter((e) => !e.resolved).length;

    // Sync status breakdown
    const syncGroups = configs.reduce<Record<SyncStatus, number>>(
        (acc, c) => { acc[c.sync_status] = (acc[c.sync_status] ?? 0) + 1; return acc; },
        { draft: 0, approved: 0, pushed: 0, error: 0 },
    );

    // ── Render ─────────────────────────────────────────────────────────────────

    return (
        <div className="b2bi-page">

            {/* ── Header ───────────────────────────────────────────── */}
            <div className="b2bi-header">
                <div>
                    <h2>Migration B2Bi — Phase 2</h2>
                    <p className="b2bi-subtitle">
                        Génération et déploiement des Trading Partners Axway B2Bi
                    </p>
                </div>
                <button
                    type="button"
                    className="trigger-btn"
                    onClick={handleTrigger}
                    disabled={triggering}
                >
                    {triggering ? 'Démarrage…' : '▶ Lancer une génération'}
                </button>
            </div>

            {triggerMsg && (
                <div className={`trigger-msg ${triggerMsg.ok ? 'trigger-msg--ok' : 'trigger-msg--error'}`}>
                    {triggerMsg.text}
                </div>
            )}

            {loading && <div className="b2bi-loading">Chargement…</div>}

            {!loading && (
                <>
                    {/* ── Phase pipeline bar ──────────────────────────── */}
                    <div className="pipeline-bar">
                        {[
                            { label: 'Inventaire CFT', phase: 1, done: true },
                            { label: 'Génération B2Bi', phase: 2, done: jobs.some((j) => j.status === 'completed'), active: jobs.some((j) => j.status === 'running') },
                            { label: 'Déploiement', phase: 3, done: syncGroups.pushed > 0, pending: syncGroups.pushed === 0 },
                        ].map((step, i) => (
                            <div
                                key={step.label}
                                className={`pipeline-step ${step.done ? 'pipeline-step--done' : step.active ? 'pipeline-step--active' : 'pipeline-step--pending'}`}
                            >
                                <div className="pipeline-step-num">{step.phase}</div>
                                <span className="pipeline-step-label">{step.label}</span>
                                {i < 2 && <div className="pipeline-step-arrow">→</div>}
                            </div>
                        ))}
                    </div>

                    {/* ── Metric cards ────────────────────────────────── */}
                    <div className="metrics-row">
                        <div className="metric-card">
                            <span className="metric-label">Partenaires inventoriés</span>
                            <strong className="metric-value">{inventoryStats?.total_partners ?? '—'}</strong>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">Prêts à générer</span>
                            <strong className="metric-value metric-value--ok">{inventoryStats?.ready_partners ?? '—'}</strong>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">Bloqués (Bucket C)</span>
                            <strong className="metric-value metric-value--error">{inventoryStats?.blocked_partners ?? '—'}</strong>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">Configs déployées</span>
                            <strong className="metric-value metric-value--pushed">{syncGroups.pushed}</strong>
                        </div>
                    </div>

                    {/* ── Main grid ───────────────────────────────────── */}
                    <div className="b2bi-grid">

                        {/* Jobs panel */}
                        <div className="panel">
                            <div className="panel-header">
                                <h3>Jobs de génération</h3>
                                <span className="panel-count">{jobs.length}</span>
                            </div>

                            {jobs.length === 0 ? (
                                <p className="empty-hint">Aucun job — lancez une génération ci-dessus.</p>
                            ) : (
                                <ul className="job-list">
                                    {jobs.map((job) => (
                                        <li
                                            key={job.id}
                                            className={`job-item ${selectedJob?.id === job.id ? 'job-item--selected' : ''}`}
                                            onClick={() => setSelectedJob(job)}
                                        >
                                            <div className="job-item-top">
                                                <span className="job-name">{job.job_name}</span>
                                                <StatusBadge status={job.status} />
                                            </div>
                                            <ProgressBar value={job.processed} total={job.total_partners} status={job.status} />
                                            <div className="job-item-meta">
                                                <span>{job.succeeded} ok · {job.failed} KO</span>
                                                <span>{formatDate(job.created_at)}</span>
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>

                        {/* Exceptions panel */}
                        <div className="panel">
                            <div className="panel-header">
                                <h3>Exceptions</h3>
                                {selectedJob && (
                                    <div className="exc-filters">
                                        {(['all', 'blocking', 'unresolved'] as const).map((f) => (
                                            <button
                                                key={f}
                                                type="button"
                                                className={`filter-btn ${excFilter === f ? 'filter-btn--active' : ''}`}
                                                onClick={() => setExcFilter(f)}
                                            >
                                                {f === 'all' ? `Toutes (${exceptions.length})` : f === 'blocking' ? `⛔ Bloquantes (${blockingCount})` : `Non résolues (${unresolvedCount})`}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {!selectedJob ? (
                                <p className="empty-hint">Sélectionnez un job pour voir ses exceptions.</p>
                            ) : filteredExceptions.length === 0 ? (
                                <p className="empty-hint">
                                    {excFilter === 'all' ? '✅ Aucune exception pour ce job.' : 'Aucune exception dans ce filtre.'}
                                </p>
                            ) : (
                                <ul className="exc-list">
                                    {filteredExceptions.map((exc) => (
                                        <li key={exc.id} className={`exc-item ${exc.resolved ? 'exc-item--resolved' : ''}`}>
                                            <div className="exc-item-top">
                                                <ExceptionBadge type={exc.exception_type} />
                                                {exc.resolved && <span className="resolved-mark">✓ résolu</span>}
                                            </div>
                                            <div className="exc-item-meta">
                                                <span className="exc-partner">{exc.partner_id}</span>
                                                {exc.field_name && <span className="exc-field">champ: {exc.field_name}</span>}
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>

                        {/* B2Bi configs panel */}
                        <div className="panel panel--wide">
                            <div className="panel-header">
                                <h3>Configs B2Bi générées</h3>
                                <div className="sync-legend">
                                    {(['draft', 'approved', 'pushed', 'error'] as SyncStatus[]).map((s) => (
                                        <span key={s} className="sync-pill">
                                            <span className={`sync-dot sync-dot--${s}`} />
                                            {s} ({syncGroups[s]})
                                        </span>
                                    ))}
                                </div>
                            </div>

                            {configs.length === 0 ? (
                                <p className="empty-hint">Aucune config générée — lancez une génération.</p>
                            ) : (
                                <div className="config-table-wrap">
                                    <table className="config-table">
                                        <thead>
                                        <tr>
                                            <th>Partenaire B2Bi</th>
                                            <th>Communauté</th>
                                            <th>Statut</th>
                                            <th>Migration ID</th>
                                            <th>Généré le</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        {configs.map((c) => (
                                            <tr key={c.migration_id}>
                                                <td className="td-name">{c.b2bi_partner_name}</td>
                                                <td>{c.community_name}</td>
                                                <td><StatusBadge status={c.sync_status} /></td>
                                                <td className="td-mono">{c.migration_id}</td>
                                                <td>{formatDate(c.created_at)}</td>
                                            </tr>
                                        ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>

                    </div>
                </>
            )}
        </div>
    );
}