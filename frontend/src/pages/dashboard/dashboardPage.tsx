import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchStats, fetchPipelineStatus, triggerPipeline, InventoryStats, PipelineStatus } from '../../services/databaseService';
import './dashboard.css';

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(iso: string | null): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('fr-FR', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    });
}

function stateLabel(state: string): { label: string; className: string } {
    switch (state) {
        case 'success':   return { label: 'Succès',     className: 'state-success' };
        case 'running':   return { label: 'En cours',   className: 'state-running' };
        case 'failed':    return { label: 'Échoué',     className: 'state-failed'  };
        case 'queued':    return { label: 'En attente', className: 'state-queued'  };
        case 'no_runs':   return { label: 'Aucun run',  className: 'state-none'    };
        default:          return { label: state,        className: 'state-none'    };
    }
}

// ── Component ─────────────────────────────────────────────────────────────────

function DashboardPage() {
    const [stats, setStats] = useState<InventoryStats | null>(null);
    const [pipeline, setPipeline] = useState<PipelineStatus | null>(null);
    const [statsLoading, setStatsLoading] = useState(true);
    const [pipelineLoading, setPipelineLoading] = useState(true);
    const [triggering, setTriggering] = useState(false);
    const [triggerMsg, setTriggerMsg] = useState<string | null>(null);

    const loadStats = useCallback(async () => {
        setStatsLoading(true);
        const data = await fetchStats();
        setStats(data);
        setStatsLoading(false);
    }, []);

    const loadPipeline = useCallback(async () => {
        setPipelineLoading(true);
        const data = await fetchPipelineStatus();
        setPipeline(data);
        setPipelineLoading(false);
    }, []);

    useEffect(() => {
        loadStats();
        loadPipeline();
    }, [loadStats, loadPipeline]);

    const handleTrigger = async () => {
        setTriggering(true);
        setTriggerMsg(null);
        const result = await triggerPipeline();
        if (result) {
            setTriggerMsg(`Run déclenché : ${result.dag_run_id} (${result.state})`);
            // Refresh pipeline status after a short delay
            setTimeout(loadPipeline, 2000);
        } else {
            setTriggerMsg('Échec du déclenchement — vérifiez Airflow.');
        }
        setTriggering(false);
    };

    const totalFlows = (stats?.flows_send ?? 0) + (stats?.flows_recv ?? 0);
    const totalTransfers = (stats?.transfers_ok ?? 0) + (stats?.transfers_nok ?? 0);
    const okPct = totalTransfers > 0
        ? Math.round((stats!.transfers_ok / totalTransfers) * 100)
        : 0;
    const nokPct = totalTransfers > 0
        ? Math.round((stats!.transfers_nok / totalTransfers) * 100)
        : 0;

    const pipelineState = pipeline ? stateLabel(pipeline.state) : null;

    return (
        <div className="dashboard-page">

            {/* ── Header ─────────────────────────────────────────── */}
            <section className="dashboard-header">
                <div>
                    <h2>Tableau de bord</h2>
                    <p>Inventaire en temps réel extrait de la base de données CFT.</p>
                </div>
                <Link to="/accueil" className="dashboard-back-link">
                    Retour à l'accueil
                </Link>
            </section>

            {/* ── Inventory metrics ──────────────────────────────── */}
            <section className="metrics-grid" aria-label="Métriques d'inventaire">
                {statsLoading ? (
                    <div className="metric-card"><span>Chargement…</span><strong>—</strong></div>
                ) : (
                    <>
                        <article className="metric-card">
                            <span>Partenaires CFT</span>
                            <strong>{stats?.partners ?? '—'}</strong>
                        </article>
                        <article className="metric-card">
                            <span>dont SSL activé</span>
                            <strong>{stats?.partners_ssl ?? '—'}</strong>
                        </article>
                        <article className="metric-card">
                            <span>Flux totaux</span>
                            <strong>{totalFlows}</strong>
                        </article>
                        <article className="metric-card">
                            <span>Transferts Copilot</span>
                            <strong>{totalTransfers}</strong>
                        </article>
                        <article className="metric-card">
                            <span>Serveurs</span>
                            <strong>{stats?.servers ?? '—'}</strong>
                        </article>
                        <article className="metric-card">
                            <span>Scripts post-transfert</span>
                            <strong>{stats?.scripts ?? '—'}</strong>
                        </article>
                    </>
                )}
            </section>

            {/* ── Detail panels ──────────────────────────────────── */}
            <section className="dashboard-grid">

                {/* Flux breakdown */}
                <article className="dashboard-panel">
                    <h3>Flux CFT</h3>
                    {statsLoading ? <p className="loading-text">Chargement…</p> : (
                        <>
                            <div className="outcome-row success">
                                <span>Send</span>
                                <strong>{stats?.flows_send ?? 0}</strong>
                            </div>
                            <div className="outcome-row pending">
                                <span>Recv</span>
                                <strong>{stats?.flows_recv ?? 0}</strong>
                            </div>
                            <div className="outcome-row">
                                <span>Avec XLATE</span>
                                <strong>{stats?.flows_xlate ?? 0}</strong>
                            </div>
                            <div className="outcome-row failed">
                                <span>TCP sans partenaire</span>
                                <strong>{stats?.tcp_without_partner ?? 0}</strong>
                            </div>
                        </>
                    )}
                </article>

                {/* Transfer outcome */}
                <article className="dashboard-panel">
                    <h3>Transferts Copilot</h3>
                    {statsLoading ? <p className="loading-text">Chargement…</p> : totalTransfers === 0 ? (
                        <p className="loading-text">Aucun transfert — Copilot sync désactivé.</p>
                    ) : (
                        <>
                            <div className="outcome-row success">
                                <span>OK</span>
                                <strong>{stats?.transfers_ok ?? 0} ({okPct}%)</strong>
                            </div>
                            <div className="outcome-row failed">
                                <span>NOK</span>
                                <strong>{stats?.transfers_nok ?? 0} ({nokPct}%)</strong>
                            </div>
                            <div className="outcome-row">
                                <span>Total</span>
                                <strong>{totalTransfers}</strong>
                            </div>
                        </>
                    )}
                </article>

                {/* Airflow pipeline status */}
                <article className="dashboard-panel">
                    <h3>Pipeline Airflow</h3>
                    {pipelineLoading ? (
                        <p className="loading-text">Chargement…</p>
                    ) : !pipeline ? (
                        <p className="loading-text">Airflow inaccessible.</p>
                    ) : (
                        <>
                            <div className="outcome-row">
                                <span>État</span>
                                <span className={`state-badge ${pipelineState?.className}`}>
                                    {pipelineState?.label}
                                </span>
                            </div>
                            <div className="outcome-row">
                                <span>Run ID</span>
                                <strong className="run-id">{pipeline.dag_run_id ?? '—'}</strong>
                            </div>
                            <div className="outcome-row">
                                <span>Démarré</span>
                                <strong>{formatDate(pipeline.start_date)}</strong>
                            </div>
                            <div className="outcome-row">
                                <span>Terminé</span>
                                <strong>{formatDate(pipeline.end_date)}</strong>
                            </div>
                        </>
                    )}

                    <div className="trigger-zone">
                        <button
                            type="button"
                            className="trigger-btn"
                            onClick={handleTrigger}
                            disabled={triggering}
                        >
                            {triggering ? 'Déclenchement…' : '▶ Lancer l\'import maintenant'}
                        </button>
                        {triggerMsg && (
                            <p className={`trigger-msg ${triggerMsg.startsWith('Échec') ? 'trigger-msg--error' : 'trigger-msg--ok'}`}>
                                {triggerMsg}
                            </p>
                        )}
                    </div>
                </article>

            </section>
        </div>
    );
}

export default DashboardPage;