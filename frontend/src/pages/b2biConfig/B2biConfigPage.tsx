import { useState, useEffect, useCallback } from 'react';
import {
    fetchB2biPartners,
    fetchB2biPartnerDeliveries,
    fetchB2biInboundFlows,
    updateB2biPartnerStatus,
    updateB2biDeliveryStatus,
    updateB2biInboundFlowStatus,
    fetchCommunities,
    triggerB2biGeneration,
    type B2biPartner,
    type B2biPartnerDelivery,
    type B2biInboundFlow,
    type Community,
    type GenerationReport,
    type MigrationStatus,
} from '../../services/api';
import './B2biConfigPage.css';

// ── Helpers ───────────────────────────────────────────────────────────────────

const STATUSES: MigrationStatus[] = ['DRAFT', 'READY', 'PUSHED', 'VALIDATED', 'MIGRATED', 'ERROR'];

const STATUS_LABELS: Record<MigrationStatus, string> = {
    DRAFT: 'Brouillon',
    READY: 'Prêt',
    PUSHED: 'Poussé',
    VALIDATED: 'Validé',
    MIGRATED: 'Migré',
    ERROR: 'Erreur',
};

const STATUS_CLASS: Record<MigrationStatus, string> = {
    DRAFT: 'badge badge--pending',
    READY: 'badge badge--ok',
    PUSHED: 'badge badge--pushed',
    VALIDATED: 'badge badge--ok',
    MIGRATED: 'badge badge--pushed',
    ERROR: 'badge badge--error',
};

function StatusBadge({ status }: { status: MigrationStatus }) {
    return <span className={STATUS_CLASS[status] ?? 'badge badge--pending'}>{STATUS_LABELS[status] ?? status}</span>;
}

function StatusSelect({
                          value,
                          onChange,
                      }: {
    value: MigrationStatus;
    onChange: (next: MigrationStatus) => void;
}) {
    return (
        <select
            className="status-select"
            value={value}
            onChange={(e) => onChange(e.target.value as MigrationStatus)}
        >
            {STATUSES.map((s) => (
                <option key={s} value={s}>{STATUS_LABELS[s]}</option>
            ))}
        </select>
    );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function B2biConfigPage() {
    const [partners, setPartners] = useState<B2biPartner[]>([]);
    const [selectedPartner, setSelectedPartner] = useState<B2biPartner | null>(null);
    const [deliveries, setDeliveries] = useState<B2biPartnerDelivery[]>([]);
    const [inboundFlows, setInboundFlows] = useState<B2biInboundFlow[]>([]);

    const [communities, setCommunities] = useState<Community[]>([]);
    const [generationCommunityId, setGenerationCommunityId] = useState<string>('');
    const [generating, setGenerating] = useState(false);
    const [generationReport, setGenerationReport] = useState<GenerationReport | null>(null);

    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState<MigrationStatus | 'all'>('all');
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    // ── Loaders ───────────────────────────────────────────────────────────────

    const loadPartners = useCallback(async () => {
        const data = await fetchB2biPartners(
            statusFilter === 'all' ? undefined : { migration_status: statusFilter },
        ).catch(() => [] as B2biPartner[]);
        setPartners(data);
        return data;
    }, [statusFilter]);

    const loadPartnerDetails = useCallback(async (partner: B2biPartner) => {
        const [dels, flows] = await Promise.all([
            fetchB2biPartnerDeliveries(partner.b2bi_partner_id).catch(() => [] as B2biPartnerDelivery[]),
            fetchB2biInboundFlows(partner.b2bi_partner_id).catch(() => [] as B2biInboundFlow[]),
        ]);
        setDeliveries(dels);
        setInboundFlows(flows);
    }, []);

    useEffect(() => {
        setLoading(true);
        loadPartners().then((data) => {
            setSelectedPartner((prev) => {
                if (prev && data.some((p) => p.b2bi_partner_id === prev.b2bi_partner_id)) return prev;
                return data[0] ?? null;
            });
            setLoading(false);
        });
    }, [loadPartners]);

    useEffect(() => {
        fetchCommunities().then((data) => {
            setCommunities(data);
            setGenerationCommunityId((prev) => prev || data[0]?.community_id || '');
        }).catch(() => setCommunities([]));
    }, []);

    useEffect(() => {
        if (selectedPartner) loadPartnerDetails(selectedPartner);
        else {
            setDeliveries([]);
            setInboundFlows([]);
        }
    }, [selectedPartner, loadPartnerDetails]);

    // ── Actions ───────────────────────────────────────────────────────────────

    const handleGenerate = async () => {
        if (!generationCommunityId) {
            setErrorMsg('Sélectionnez une communauté cible avant de lancer la génération.');
            return;
        }
        setGenerating(true);
        setErrorMsg(null);
        setGenerationReport(null);
        try {
            const report = await triggerB2biGeneration(generationCommunityId);
            setGenerationReport(report);
            const updated = await loadPartners();
            if (selectedPartner) {
                const fresh = updated.find((p) => p.b2bi_partner_id === selectedPartner.b2bi_partner_id);
                if (fresh) setSelectedPartner(fresh);
            } else if (updated.length > 0) {
                setSelectedPartner(updated[0]);
            }
        } catch (e: any) {
            setErrorMsg(e.message || 'Échec de la génération.');
        } finally {
            setGenerating(false);
        }
    };

    const handlePartnerStatusChange = async (partner: B2biPartner, next: MigrationStatus) => {
        setErrorMsg(null);
        try {
            await updateB2biPartnerStatus(partner.b2bi_partner_id, next);
            const updated = await loadPartners();
            const fresh = updated.find((p) => p.b2bi_partner_id === partner.b2bi_partner_id);
            if (fresh) setSelectedPartner(fresh);
        } catch (e: any) {
            setErrorMsg(e.message || 'Échec de la mise à jour du statut.');
        }
    };

    const handleDeliveryStatusChange = async (delivery: B2biPartnerDelivery, next: MigrationStatus) => {
        setErrorMsg(null);
        try {
            await updateB2biDeliveryStatus(delivery.partner_delivery_id, next);
            if (selectedPartner) loadPartnerDetails(selectedPartner);
        } catch (e: any) {
            setErrorMsg(e.message || 'Échec de la mise à jour du statut.');
        }
    };

    const handleFlowStatusChange = async (flow: B2biInboundFlow, next: MigrationStatus) => {
        setErrorMsg(null);
        try {
            await updateB2biInboundFlowStatus(flow.inbound_flow_id, next);
            if (selectedPartner) loadPartnerDetails(selectedPartner);
        } catch (e: any) {
            setErrorMsg(e.message || 'Échec de la mise à jour du statut.');
        }
    };

    // ── Derived data ──────────────────────────────────────────────────────────

    const statusGroups = partners.reduce(
        (acc, p) => { acc[p.migration_status] = (acc[p.migration_status] ?? 0) + 1; return acc; },
        { DRAFT: 0, READY: 0, PUSHED: 0, VALIDATED: 0, MIGRATED: 0, ERROR: 0 } as Record<MigrationStatus, number>,
    );

    // ── Render ────────────────────────────────────────────────────────────────

    return (
        <div className="b2bi-page">

            {/* ── Header ─────────────────────────────────────────────────── */}
            <div className="b2bi-header">
                <div>
                    <h2>Migration B2Bi</h2>
                    <p className="b2bi-subtitle">
                        Partenaires, livraisons et flux entrants B2Bi, et leur statut de migration
                    </p>
                </div>
                <div className="generation-controls">
                    <select
                        className="status-select"
                        value={generationCommunityId}
                        onChange={(e) => setGenerationCommunityId(e.target.value)}
                        disabled={generating || communities.length === 0}
                    >
                        {communities.length === 0 && <option value="">Aucune communauté</option>}
                        {communities.map((c) => (
                            <option key={c.community_id} value={c.community_id}>{c.name}</option>
                        ))}
                    </select>
                    <button
                        type="button"
                        className="trigger-btn"
                        onClick={handleGenerate}
                        disabled={generating || !generationCommunityId}
                    >
                        {generating ? 'Génération en cours…' : '▶ Générer la config B2Bi depuis CFT'}
                    </button>
                </div>
            </div>

            {generationReport && (
                <div className="trigger-msg trigger-msg--ok">
                    {generationReport.partners_processed} partenaire(s) traité(s) — {generationReport.partners_ready} prêt(s),{' '}
                    {generationReport.partners_draft} brouillon(s), {generationReport.partners_error} en erreur ·{' '}
                    {generationReport.deliveries_created} livraison(s) créée(s) / {generationReport.deliveries_updated} mise(s) à jour ·{' '}
                    {generationReport.inbound_flows_created} flux entrant(s) créé(s) / {generationReport.inbound_flows_updated} mis à jour
                    {generationReport.errors.length > 0 && (
                        <ul className="generation-errors">
                            {generationReport.errors.map((err, i) => <li key={i}>{err}</li>)}
                        </ul>
                    )}
                </div>
            )}

            {errorMsg && <div className="trigger-msg trigger-msg--error">{errorMsg}</div>}

            {loading && <div className="b2bi-loading">Chargement…</div>}

            {!loading && (
                <>
                    {/* ── Status legend / filter ─────────────────────────── */}
                    <div className="sync-legend">
                        <button
                            type="button"
                            className={`filter-btn ${statusFilter === 'all' ? 'filter-btn--active' : ''}`}
                            onClick={() => setStatusFilter('all')}
                        >
                            Tous ({partners.length})
                        </button>
                        {STATUSES.map((s) => (
                            <button
                                key={s}
                                type="button"
                                className={`filter-btn ${statusFilter === s ? 'filter-btn--active' : ''}`}
                                onClick={() => setStatusFilter(s)}
                            >
                                {STATUS_LABELS[s]} ({statusGroups[s]})
                            </button>
                        ))}
                    </div>

                    {/* ── Main grid ──────────────────────────────────────── */}
                    <div className="b2bi-grid">

                        {/* Partners panel */}
                        <div className="panel">
                            <div className="panel-header">
                                <h3>Partenaires B2Bi</h3>
                                <span className="panel-count">{partners.length}</span>
                            </div>

                            {partners.length === 0 ? (
                                <p className="empty-hint">Aucun partenaire pour ce filtre.</p>
                            ) : (
                                <ul className="job-list">
                                    {partners.map((partner) => (
                                        <li
                                            key={partner.b2bi_partner_id}
                                            className={`job-item ${selectedPartner?.b2bi_partner_id === partner.b2bi_partner_id ? 'job-item--selected' : ''}`}
                                            onClick={() => setSelectedPartner(partner)}
                                        >
                                            <div className="job-item-top">
                                                <span className="job-name">{partner.party_name}</span>
                                                <StatusBadge status={partner.migration_status} />
                                            </div>
                                            <div className="job-item-meta">
                                                <span>{partner.partner_code}</span>
                                                <span>{partner.community_id}</span>
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>

                        {/* Deliveries panel */}
                        <div className="panel panel--wide">
                            <div className="panel-header">
                                <h3>Livraisons</h3>
                                <span className="panel-count">{deliveries.length}</span>
                            </div>

                            {!selectedPartner ? (
                                <p className="empty-hint">Sélectionnez un partenaire pour voir ses livraisons.</p>
                            ) : deliveries.length === 0 ? (
                                <p className="empty-hint">Aucune livraison pour ce partenaire.</p>
                            ) : (
                                <div className="config-table-wrap">
                                    <table className="config-table">
                                        <thead>
                                        <tr>
                                            <th>Nom</th>
                                            <th>Hôte</th>
                                            <th>Port</th>
                                            <th>IDF</th>
                                            <th>Statut</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        {deliveries.map((d) => (
                                            <tr key={d.partner_delivery_id}>
                                                <td className="td-name">{d.friendly_name}</td>
                                                <td className="td-mono">{d.host ?? '—'}</td>
                                                <td className="td-mono">{d.port ?? '—'}</td>
                                                <td className="td-mono">{d.idf}</td>
                                                <td>
                                                    <StatusSelect
                                                        value={d.migration_status}
                                                        onChange={(next) => handleDeliveryStatusChange(d, next)}
                                                    />
                                                </td>
                                            </tr>
                                        ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>

                        {/* Inbound flows panel */}
                        <div className="panel panel--wide">
                            <div className="panel-header">
                                <h3>Flux entrants</h3>
                                <span className="panel-count">{inboundFlows.length}</span>
                            </div>

                            {!selectedPartner ? (
                                <p className="empty-hint">Sélectionnez un partenaire pour voir ses flux.</p>
                            ) : inboundFlows.length === 0 ? (
                                <p className="empty-hint">Aucun flux entrant pour ce partenaire.</p>
                            ) : (
                                <div className="config-table-wrap">
                                    <table className="config-table">
                                        <thead>
                                        <tr>
                                            <th>IDF</th>
                                            <th>Fichier</th>
                                            <th>Renommage</th>
                                            <th>Statut</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        {inboundFlows.map((f) => (
                                            <tr key={f.inbound_flow_id}>
                                                <td className="td-mono">{f.idf}</td>
                                                <td className="td-mono">{f.fname ?? '—'}</td>
                                                <td className="td-mono">{f.rename_rule ?? '—'}</td>
                                                <td>
                                                    <StatusSelect
                                                        value={f.migration_status}
                                                        onChange={(next) => handleFlowStatusChange(f, next)}
                                                    />
                                                </td>
                                            </tr>
                                        ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>

                        {/* Partner detail / status control panel */}
                        {selectedPartner && (
                            <div className="panel panel--wide">
                                <div className="panel-header">
                                    <h3>Statut du partenaire</h3>
                                </div>
                                <div className="metrics-row">
                                    <div className="metric-card">
                                        <span className="metric-label">Partenaire</span>
                                        <strong className="metric-value">{selectedPartner.party_name}</strong>
                                    </div>
                                    <div className="metric-card">
                                        <span className="metric-label">Code</span>
                                        <strong className="metric-value">{selectedPartner.partner_code}</strong>
                                    </div>
                                    <div className="metric-card">
                                        <span className="metric-label">Statut</span>
                                        <StatusSelect
                                            value={selectedPartner.migration_status}
                                            onChange={(next) => handlePartnerStatusChange(selectedPartner, next)}
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                    </div>
                </>
            )}
        </div>
    );
}