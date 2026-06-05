import { Link } from 'react-router-dom';
import './dashboard.css';

const metrics = [
    { label: 'Total migrations', value: '48' },
    { label: 'Succeeded', value: '36' },
    { label: 'Failed', value: '5' },
    { label: 'In progress', value: '7' },
];

const servers = [
    { name: 'CFT-PROD-01', type: 'Source', status: 'Connected' },
    { name: 'CFT-UAT-02', type: 'Source', status: 'Connected' },
    { name: 'B2BI-PROD-01', type: 'Target', status: 'Ready' },
    { name: 'B2BI-UAT-02', type: 'Target', status: 'Syncing' },
];

const activities = [
    'Partner flows migrated from CFT-PROD-01',
    'B2BI-UAT-02 synchronization started',
    '5 migrations require manual validation',
    'Production readiness checks completed',
];

function DashboardPage() {
    return (
        <div className="dashboard-page">
            <section className="dashboard-header">
                <div>
                    <h2>Tableau de bord</h2>
                    <p>Aperçu statique des migrations montrant l'état actuel du pipeline et l'activité de migration récente.</p>
                </div>

                <Link to="/accueil" className="dashboard-back-link">
                    Retour à la page d'accueil
                </Link>
            </section>

            <section className="metrics-grid" aria-label="Migration metrics">
                {metrics.map((metric) => (
                    <article className="metric-card" key={metric.label}>
                        <span>{metric.label}</span>
                        <strong>{metric.value}</strong>
                    </article>
                ))}
            </section>

            <section className="dashboard-grid">
                <article className="dashboard-panel">
                    <h3>Migration outcome</h3>

                    <div className="outcome-row success">
                        <span>Réussi</span>
                        <strong>75%</strong>
                    </div>

                    <div className="outcome-row failed">
                        <span>Échoué</span>
                        <strong>10%</strong>
                    </div>

                    <div className="outcome-row pending">
                        <span>En cours</span>
                        <strong>15%</strong>
                    </div>
                </article>

                <article className="dashboard-panel">
                    <h3>Servers</h3>

                    <div className="server-list">
                        {servers.map((server) => (
                            <div className="server-item" key={server.name}>
                                <div>
                                    <strong>{server.name}</strong>
                                    <span>{server.type}</span>
                                </div>
                                <span className="server-status">{server.status}</span>
                            </div>
                        ))}
                    </div>
                </article>

                <article className="dashboard-panel activity-panel">
                    <h3>Recent activity</h3>

                    <ul>
                        {activities.map((activity) => (
                            <li key={activity}>{activity}</li>
                        ))}
                    </ul>
                </article>
            </section>
        </div>
    );
}

export default DashboardPage;