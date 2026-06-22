import { FormEvent, useState } from 'react';
import { sshPull, type SshPullReport } from '../../services/api';
import './ServerConfigPage.css';

// ── Types ─────────────────────────────────────────────────────────────────────

type PullState = 'idle' | 'loading' | 'success' | 'error';

// ── Component ─────────────────────────────────────────────────────────────────

function ServerConfigPage() {
    const [state, setState] = useState<PullState>('idle');
    const [report, setReport] = useState<SshPullReport | null>(null);

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const form = new FormData(e.currentTarget);

        const body = {
            server_id:       (form.get('server_id') as string).trim(),
            host:            (form.get('host') as string).trim(),
            port:            parseInt(form.get('port') as string, 10) || 22,
            username:        (form.get('username') as string).trim(),
            password:        form.get('password') as string,
            remote_conf_dir: (form.get('remote_conf_dir') as string).trim(),
            environment:     (form.get('environment') as string).trim() || 'production',
        };

        setState('loading');
        setReport(null);

        try {
            const result = await sshPull(body);
            setReport(result);
            setState(result.error ? 'error' : 'success');
        } catch (err: any) {
            setReport({
                server_id: body.server_id,
                host: body.host,
                files_pulled: 0,
                filenames: [],
                partner_parsed: 0,
                partner_upserted: 0,
                tcp_parsed: 0,
                tcp_upserted: 0,
                send_parsed: 0,
                recv_parsed: 0,
                flow_upserted: 0,
                tcp_missing_partner: 0,
                error: err.message || 'Erreur inconnue',
            });
            setState('error');
        }
    };

    const isLoading = state === 'loading';

    return (
        <div className="server-config-page">
            <div className="page-header">
                <h2>Extraction SSH CFT</h2>
                <p>
                    Connectez-vous à un serveur CFT distant, téléchargez les fichiers
                    de configuration et lancez l'import automatiquement.
                </p>
            </div>

            <div className="page-content">
                <section className="ssh-form-card">
                    <h3>Connexion SSH</h3>

                    <form className="ssh-form" onSubmit={handleSubmit}>
                        <div className="form-grid">

                            {/* Server label */}
                            <label className="form-field">
                                <span>Identifiant serveur</span>
                                <input
                                    type="text"
                                    name="server_id"
                                    placeholder="prod1"
                                    pattern="[A-Za-z0-9_\-]{1,50}"
                                    title="Lettres, chiffres, tirets et underscores uniquement"
                                    required
                                />
                                <small>Utilisé comme nom de dossier local (ex: prod1, dmz1)</small>
                            </label>

                            {/* Environment */}
                            <label className="form-field">
                                <span>Environnement</span>
                                <input
                                    type="text"
                                    name="environment"
                                    placeholder="production"
                                    defaultValue="production"
                                />
                            </label>

                            {/* Host */}
                            <label className="form-field">
                                <span>Hôte SSH</span>
                                <input
                                    type="text"
                                    name="host"
                                    placeholder="cft-prod.company.local"
                                    required
                                />
                            </label>

                            {/* Port */}
                            <label className="form-field">
                                <span>Port</span>
                                <input
                                    type="number"
                                    name="port"
                                    placeholder="22"
                                    defaultValue="22"
                                    min={1}
                                    max={65535}
                                />
                            </label>

                            {/* Username */}
                            <label className="form-field">
                                <span>Utilisateur SSH</span>
                                <input
                                    type="text"
                                    name="username"
                                    placeholder="cftadmin"
                                    required
                                    autoComplete="username"
                                />
                            </label>

                            {/* Password */}
                            <label className="form-field">
                                <span>Mot de passe</span>
                                <input
                                    type="password"
                                    name="password"
                                    placeholder="••••••••"
                                    required
                                    autoComplete="current-password"
                                />
                            </label>

                            {/* Remote conf dir */}
                            <label className="form-field form-field--full">
                                <span>Répertoire des fichiers conf sur le serveur distant</span>
                                <input
                                    type="text"
                                    name="remote_conf_dir"
                                    placeholder="/opt/cft/data  ou  C:\CFT\data"
                                    required
                                />
                                <small>
                                    Dossier contenant les fichiers <code>conf_cft.*.txt</code> sur le serveur CFT
                                </small>
                            </label>

                        </div>

                        <div className="form-actions">
                            <button
                                type="submit"
                                className="action-btn action-btn--primary"
                                disabled={isLoading}
                            >
                                {isLoading ? 'Extraction en cours…' : '▶ Extraire et importer'}
                            </button>
                        </div>
                    </form>
                </section>

                {/* ── Result panel ─────────────────────────────────────────── */}
                {report && (
                    <section className="cft-results-card">
                        <div className="results-header">
                            <div>
                                <h3>
                                    {state === 'error' && !report.files_pulled
                                        ? 'Connexion échouée'
                                        : `Résultats — ${report.server_id}`}
                                </h3>
                                <p className="results-host">{report.host}</p>
                            </div>
                            <span className={`pull-status pull-status--${state === 'success' ? 'success' : 'error'}`}>
                                {state === 'success' ? '✓ Succès' : '✕ Erreur'}
                            </span>
                        </div>

                        {/* Error message */}
                        {report.error && (
                            <div className="pull-error">
                                {report.error}
                            </div>
                        )}

                        {/* Files pulled */}
                        {report.files_pulled > 0 && (
                            <>
                                <div className="results-section-title">
                                    Fichiers téléchargés ({report.files_pulled})
                                </div>
                                <ul className="file-list">
                                    {report.filenames.map((f) => (
                                        <li key={f}>
                                            <code>{f}</code>
                                        </li>
                                    ))}
                                </ul>

                                {/* Import stats */}
                                <div className="results-section-title">Résultats d'import</div>
                                <div className="import-stats">
                                    <div className="stat-row">
                                        <span>Partenaires parsés</span>
                                        <strong>{report.partner_parsed}</strong>
                                    </div>
                                    <div className="stat-row">
                                        <span>Partenaires upsertés</span>
                                        <strong>{report.partner_upserted}</strong>
                                    </div>
                                    <div className="stat-row">
                                        <span>Flux SEND parsés</span>
                                        <strong>{report.send_parsed}</strong>
                                    </div>
                                    <div className="stat-row">
                                        <span>Flux RECV parsés</span>
                                        <strong>{report.recv_parsed}</strong>
                                    </div>
                                    <div className="stat-row">
                                        <span>Flux upsertés</span>
                                        <strong>{report.flow_upserted}</strong>
                                    </div>
                                    <div className="stat-row">
                                        <span>TCP upsertés</span>
                                        <strong>{report.tcp_upserted}</strong>
                                    </div>
                                    {report.tcp_missing_partner > 0 && (
                                        <div className="stat-row stat-row--warn">
                                            <span>TCP sans partenaire (staging)</span>
                                            <strong>{report.tcp_missing_partner}</strong>
                                        </div>
                                    )}
                                </div>
                            </>
                        )}
                    </section>
                )}
            </div>
        </div>
    );
}

export default ServerConfigPage;