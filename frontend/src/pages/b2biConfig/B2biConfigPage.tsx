import { useState, useEffect, useCallback, useRef } from 'react';
import {
    triggerGeneration,
    fetchGenerationJobs,
    fetchJobConfigs,
    fetchExceptions,
    fetchExceptionSummary,
    fetchMappingRules,
    approveConfig,
    resolveException,
    toggleMappingRule,
    type GenerationJob,
    type B2biConfig,
    type ExceptionLog,
    type ExceptionSummary,
    type MappingRule,
} from '../../services/api';
import './B2biConfigPage.css';

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('fr-FR', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    });
}

function jobProgressPct(job: GenerationJob): number {
    if (!job.partners_total) return 0;
    return Math.round(((job.partners_ok + job.partners_blocked) / job.partners_total) * 100);
}

// ── Sub-components ────────────────────────────────────────────────────────────

function JobBadge({ status }: { status: GenerationJob['status'] }) {
    const map: Record<string, string> = {
        PENDING:     'badge badge--pending',
        IN_PROGRESS: 'badge badge--running',
        COMPLETED:   'badge badge--ok',
        FAILED:      'badge badge--error',
    };
    const labels: Record<string, string> = {
        PENDING:     'En attente',
        IN_PROGRESS: 'En cours',
        COMPLETED:   'Terminé',
        FAILED:      'Échoué',
    };
    return <span className={map[status] ?? 'badge badge--pending'}>{labels[status] ?? status}</span>;
}

function SyncBadge({ status }: { status: B2biConfig['sync_status'] }) {
    const map: Record<string, string> = {
        PENDING:  'badge badge--pending',
        APPROVED: 'badge badge--ok',
        DEPLOYED: 'badge badge--pushed',
        FAILED:   'badge badge--error',
    };
    const labels: Record<string, string> = {
        PENDING:  'Brouillon',
        APPROVED: 'Approuvé',
        DEPLOYED: 'Déployé',
        FAILED:   'Erreur',
    };
    return <span className={map[status] ?? 'badge badge--pending'}>{labels[status] ?? status}</span>;
}

function ProgressBar({ job }: { job: GenerationJob }) {
    const pct = jobProgressPct(job);
    const cls = job.status === 'COMPLETED' ? 'completed'
        : job.status === 'FAILED'    ? 'failed'
            : job.status === 'IN_PROGRESS' ? 'running'
                : 'pending';
    return (
        <div className="progress-wrap">
            <div className="progress-track">
                <div className={`progress-fill progress-fill--${cls}`} style={{ width: `${pct}%` }} />
            </div>
            <span className="progress-label">{pct}%</span>
        </div>
    );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function B2biConfigPage() {
    const [jobs, setJobs] = useState<GenerationJob[]>([]);
    const [selectedJob, setSelectedJob] = useState<GenerationJob | null>(null);
    const [configs, setConfigs] = useState<B2biConfig[]>([]);
    const [exceptions, setExceptions] = useState<ExceptionLog[]>([]);
    const [summary, setSummary] = useState<ExceptionSummary | null>(null);
    const [rules, setRules] = useState<MappingRule[]>([]);

    const [loading, setLoading] = useState(true);
    const [triggering, setTriggering] = useState(false);
    const [triggerMsg, setTriggerMsg] = useState<{ text: string; ok: boolean } | null>(null);
    const [excFilter, setExcFilter] = useState<'all' | 'BLOCKING' | 'unresolved'>('all');

    const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

    // ── Loaders ───────────────────────────────────────────────────────────────

    const loadJobs = useCallback(async () => {
        const data = await fetchGenerationJobs().catch(() => [] as GenerationJob[]);
        setJobs(data);
        return data;
    }, []);

    const loadJobDetails = useCallback(async (job: GenerationJob) => {
        const [cfgs, excs, sum] = await Promise.all([
            fetchJobConfigs(job.id).catch(() => [] as B2biConfig[]),
            fetchExceptions({ job_id: job.id }).catch(() => [] as ExceptionLog[]),
            fetchExceptionSummary(job.id).catch(() => null),
        ]);
        setConfigs(cfgs);
        setExceptions(excs);
        setSummary(sum);
    }, []);

    const loadRules = useCallback(async () => {
        const data = await fetchMappingRules().catch(() => [] as MappingRule[]);
        setRules(data);
    }, []);

    // Initial load
    useEffect(() => {
        setLoading(true);
        Promise.all([loadJobs(), loadRules()]).then(([data]) => {
            if (data.length > 0) {
                setSelectedJob(data[0]);
            }
            setLoading(false);
        });
    }, [loadJobs, loadRules]);

    // Load job details when selection changes
    useEffect(() => {
        if (selectedJob) loadJobDetails(selectedJob);
    }, [selectedJob, loadJobDetails]);

    // Poll while a job is active
    useEffect(() => {
        const isActive = jobs.some(
            (j) => j.status === 'IN_PROGRESS' || j.status === 'PENDING',
        );
        if (isActive && !pollingRef.current) {
            pollingRef.current = setInterval(async () => {
                const updated = await loadJobs();
                if (selectedJob) {
                    const fresh = updated.find((j) => j.id === selectedJob.id);
                    if (fresh) {
                        setSelectedJob(fresh);
                        loadJobDetails(fresh);
                    }
                }
            }, 4000);
        } else if (!isActive && pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
        }
        return () => {
            if (pollingRef.current) clearInterval(pollingRef.current);
        };
    }, [jobs, selectedJob, loadJobs, loadJobDetails]);

    // ── Actions ───────────────────────────────────────────────────────────────

    const handleTrigger = async () => {
        setTriggering(true);
        setTriggerMsg(null);
        try {
            const report = await triggerGeneration();
            setTriggerMsg({
                text: `Job #${report.job_id} terminé — ${report.partners_ok} OK, ${report.partners_blocked} bloqués, ${report.exceptions_logged} exceptions.`,
                ok: true,
            });
            const updated = await loadJobs();
            const fresh = updated.find((j) => j.id === report.job_id);
            if (fresh) {
                setSelectedJob(fresh);
                loadJobDetails(fresh);
            }
        } catch (e: any) {
            setTriggerMsg({ text: e.message || 'Échec du déclenchement.', ok: false });
        } finally {
            setTriggering(false);
        }
    };

    const handleApprove = async (config: B2biConfig) => {
        try {
            await approveConfig(config.job_id, config.id);
            if (selectedJob) loadJobDetails(selectedJob);
        } catch (e: any) {
            alert(`Erreur : ${e.message}`);
        }
    };

    const handleResolve = async (exc: ExceptionLog) => {
        try {
            await resolveException(exc.id);
            if (selectedJob) loadJobDetails(selectedJob);
        } catch (e: any) {
            alert(`Erreur : ${e.message}`);
        }
    };

    const handleToggleRule = async (rule: MappingRule) => {
        try {
            const res = await toggleMappingRule(rule.id);
            setRules((prev) =>
                prev.map((r) => (r.id === rule.id ? { ...r, is_active: res.is_active } : r)),
            );
        } catch (e: any) {
            alert(`Erreur : ${e.message}`);
        }
    };

    // ── Derived data ──────────────────────────────────────────────────────────

    const filteredExceptions = exceptions.filter((e) => {
        if (excFilter === 'BLOCKING') return e.severity === 'BLOCKING';
        if (excFilter === 'unresolved') return !e.resolved;
        return true;
    });

    const syncGroups = configs.reduce(
        (acc, c) => { acc[c.sync_status] = (acc[c.sync_status] ?? 0) + 1; return acc; },
        { PENDING: 0, APPROVED: 0, DEPLOYED: 0, FAILED: 0 } as Record<B2biConfig['sync_status'], number>,
    );

    // ── Render ────────────────────────────────────────────────────────────────

    return (
        <div className="b2bi-page">

            {/* ── Header ─────────────────────────────────────────────────── */}
            <div className="b2bi-header">
                <div>
                    <h2>Migration B2Bi — Phase 2</h2>
                    <p className="b2bi-subtitle">
                        Génération et déploiement des configurations Trading Partner Axway B2Bi
                    </p>
                </div>
                <button
                    type="button"
                    className="trigger-btn"
                    onClick={handleTrigger}
                    disabled={triggering}
                >
                    {triggering ? 'Génération en cours…' : '▶ Lancer une génération'}
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
                    {/* ── Pipeline bar ────────────────────────────────────── */}
                    <div className="pipeline-bar">
                        {[
                            { label: 'Inventaire CFT',  phase: 1, done: true },
                            {
                                label: 'Génération B2Bi', phase: 2,
                                done: jobs.some((j) => j.status === 'COMPLETED'),
                                active: jobs.some((j) => j.status === 'IN_PROGRESS'),
                            },
                            { label: 'Déploiement', phase: 3, done: syncGroups.DEPLOYED > 0 },
                        ].map((step, i) => (
                            <div
                                key={step.label}
                                className={`pipeline-step ${
                                    step.done   ? 'pipeline-step--done'
                                        : step.active ? 'pipeline-step--active'
                                            : ''
                                }`}
                            >
                                <div className="pipeline-step-num">{step.phase}</div>
                                <span className="pipeline-step-label">{step.label}</span>
                                {i < 2 && <div className="pipeline-step-arrow">→</div>}
                            </div>
                        ))}
                    </div>

                    {/* ── Metric cards ───────────────────────────────────── */}
                    {selectedJob && (
                        <div className="metrics-row">
                            <div className="metric-card">
                                <span className="metric-label">Partenaires total</span>
                                <strong className="metric-value">{selectedJob.partners_total}</strong>
                            </div>
                            <div className="metric-card">
                                <span className="metric-label">Générés (OK)</span>
                                <strong className="metric-value metric-value--ok">{selectedJob.partners_ok}</strong>
                            </div>
                            <div className="metric-card">
                                <span className="metric-label">Bloqués</span>
                                <strong className="metric-value metric-value--error">{selectedJob.partners_blocked}</strong>
                            </div>
                            <div className="metric-card">
                                <span className="metric-label">Exceptions bloquantes</span>
                                <strong className="metric-value metric-value--error">
                                    {summary ? summary.blocking_open : '—'}
                                </strong>
                            </div>
                            <div className="metric-card">
                                <span className="metric-label">Configs approuvées</span>
                                <strong className="metric-value metric-value--pushed">{syncGroups.APPROVED}</strong>
                            </div>
                        </div>
                    )}

                    {/* ── Main grid ──────────────────────────────────────── */}
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
                                                <span className="job-name">Job #{job.id}</span>
                                                <JobBadge status={job.status} />
                                            </div>
                                            <ProgressBar job={job} />
                                            <div className="job-item-meta">
                                                <span>{job.partners_ok} ok · {job.partners_blocked} bloqués</span>
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
                                        {(['all', 'BLOCKING', 'unresolved'] as const).map((f) => (
                                            <button
                                                key={f}
                                                type="button"
                                                className={`filter-btn ${excFilter === f ? 'filter-btn--active' : ''}`}
                                                onClick={() => setExcFilter(f)}
                                            >
                                                {f === 'all'
                                                    ? `Toutes (${exceptions.length})`
                                                    : f === 'BLOCKING'
                                                        ? `⛔ Bloquantes (${summary?.blocking_open ?? 0})`
                                                        : `Non résolues (${exceptions.filter((e) => !e.resolved).length})`}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {!selectedJob ? (
                                <p className="empty-hint">Sélectionnez un job pour voir ses exceptions.</p>
                            ) : filteredExceptions.length === 0 ? (
                                <p className="empty-hint">
                                    {excFilter === 'all'
                                        ? '✅ Aucune exception pour ce job.'
                                        : 'Aucune exception dans ce filtre.'}
                                </p>
                            ) : (
                                <ul className="exc-list">
                                    {filteredExceptions.map((exc) => (
                                        <li
                                            key={exc.id}
                                            className={`exc-item ${exc.resolved ? 'exc-item--resolved' : ''}`}
                                        >
                                            <div className="exc-item-top">
                                                <span className={`exc-badge exc-badge--${exc.severity === 'BLOCKING' ? 'blocking' : 'warning'}`}>
                                                    {exc.severity === 'BLOCKING' ? '⛔ ' : '⚠ '}
                                                    {exc.exception_type.replace(/_/g, ' ')}
                                                </span>
                                                {exc.resolved
                                                    ? <span className="resolved-mark">✓ résolu</span>
                                                    : (
                                                        <button
                                                            type="button"
                                                            className="action-btn-sm"
                                                            onClick={() => handleResolve(exc)}
                                                        >
                                                            Résoudre
                                                        </button>
                                                    )}
                                            </div>
                                            <div className="exc-item-meta">
                                                <span className="exc-partner">{exc.partner_id}</span>
                                                <span className="exc-field" title={exc.message}>
                                                    {exc.message.length > 60
                                                        ? exc.message.slice(0, 57) + '…'
                                                        : exc.message}
                                                </span>
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
                                    {(['PENDING', 'APPROVED', 'DEPLOYED', 'FAILED'] as B2biConfig['sync_status'][]).map((s) => (
                                        <span key={s} className="sync-pill">
                                            <span className={`sync-dot sync-dot--${s.toLowerCase()}`} />
                                            {s.toLowerCase()} ({syncGroups[s]})
                                        </span>
                                    ))}
                                </div>
                            </div>

                            {!selectedJob ? (
                                <p className="empty-hint">Sélectionnez un job pour voir ses configs.</p>
                            ) : configs.length === 0 ? (
                                <p className="empty-hint">Aucune config générée pour ce job.</p>
                            ) : (
                                <div className="config-table-wrap">
                                    <table className="config-table">
                                        <thead>
                                        <tr>
                                            <th>Partenaire</th>
                                            <th>Statut</th>
                                            <th>Généré le</th>
                                            <th>Approuvé le</th>
                                            <th></th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        {configs.map((c) => (
                                            <tr key={c.id}>
                                                <td className="td-name">{c.partner_id}</td>
                                                <td><SyncBadge status={c.sync_status} /></td>
                                                <td>{formatDate(c.generated_at)}</td>
                                                <td>{formatDate(c.approved_at)}</td>
                                                <td>
                                                    {c.sync_status === 'PENDING' && (
                                                        <button
                                                            type="button"
                                                            className="action-btn-sm action-btn-sm--primary"
                                                            onClick={() => handleApprove(c)}
                                                        >
                                                            Approuver
                                                        </button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>

                        {/* Mapping rules panel */}
                        <div className="panel panel--wide">
                            <div className="panel-header">
                                <h3>Règles de mapping</h3>
                                <span className="panel-count">
                                    {rules.filter((r) => r.is_active).length} actives / {rules.length}
                                </span>
                            </div>

                            {rules.length === 0 ? (
                                <p className="empty-hint">Aucune règle — exécutez le script SQL 010.</p>
                            ) : (
                                <div className="config-table-wrap">
                                    <table className="config-table">
                                        <thead>
                                        <tr>
                                            <th>Nom</th>
                                            <th>Source</th>
                                            <th>Cible</th>
                                            <th>Type</th>
                                            <th>Actif</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        {rules.map((rule) => (
                                            <tr key={rule.id}>
                                                <td className="td-name">{rule.rule_name}</td>
                                                <td className="td-mono">{rule.source_field ?? '—'}</td>
                                                <td className="td-mono">{rule.target_field}</td>
                                                <td>{rule.transform_type}</td>
                                                <td>
                                                    <button
                                                        type="button"
                                                        className={`toggle-btn ${rule.is_active ? 'toggle-btn--on' : 'toggle-btn--off'}`}
                                                        onClick={() => handleToggleRule(rule)}
                                                    >
                                                        {rule.is_active ? 'Oui' : 'Non'}
                                                    </button>
                                                </td>
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