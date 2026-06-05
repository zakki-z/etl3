import { Link } from 'react-router-dom';
import './B2biConfigPage.css';

const migrationSteps = [
    { label: 'CFT inventory', status: 'done' },
    { label: 'Flow mapping', status: 'done' },
    { label: 'B2BI configuration', status: 'active' },
    { label: 'Partner validation', status: 'pending' },
    { label: 'Go-live', status: 'pending' },
];

const migrationLogs = [
    '09:00 - CFT transfer flows extracted successfully.',
    '09:20 - Partners and protocols mapped to B2BI entities.',
    '10:05 - B2BI configuration package generation started.',
    '10:30 - Waiting for validation before partner testing.',
];

function B2biConfigPage() {
    return (
        <div className="migration-page">
            <section className="migration-hero">
                <h2>Migration Axway CFT a Axway B2BI</h2>
                <p>
                    Aperçu statique des migrations montrant l'état actuel du pipeline et l'activité de migration récente.
                </p>
            </section>

            <section className="migration-pipeline" aria-label="Migration pipeline">
                {migrationSteps.map((step, index) => (
                    <div className={`migration-step ${step.status}`} key={step.label}>
                        <span className="step-index">{index + 1}</span>
                        <span>{step.label}</span>
                    </div>
                ))}
            </section>

            <section className="migration-log">
                <div className="log-header">
                    <h3>Logs de migration</h3>
                    <span>Progrès: 45%</span>
                </div>

                <div className="progress-bar">
                    <div className="progress-value" />
                </div>

                <ul>
                    {migrationLogs.map((log) => (
                        <li key={log}>{log}</li>
                    ))}
                </ul>
            </section>

            <Link to="/accueil" className="back-link">
                Retour à la page d'accueil
            </Link>
        </div>
    );
}

export default B2biConfigPage;