import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import './ServerConfigPage.css';

const mockCftData = [
    {
        id: 'FLOW-001',
        partner: 'BANK_PARTNER_A',
        direction: 'SEND',
        filePattern: 'PAYMENTS_*.xml',
        status: 'Ready',
    },
    {
        id: 'FLOW-002',
        partner: 'ERP_SYSTEM',
        direction: 'RECEIVE',
        filePattern: 'ORDERS_*.csv',
        status: 'Ready',
    },
    {
        id: 'FLOW-003',
        partner: 'ARCHIVE_SERVER',
        direction: 'SEND',
        filePattern: 'REPORT_*.zip',
        status: 'Inactive',
    },
];

const ServerConfigPage = () => {
    const [hasExtracted, setHasExtracted] = useState(false);
    const [isExtracting, setIsExtracting] = useState(false);

    const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        setIsExtracting(true);
        setHasExtracted(false);

        window.setTimeout(() => {
            setIsExtracting(false);
            setHasExtracted(true);
        }, 800);
    };

    return (
        <div className="server-config-page">
            <div className="page-header">
                <h2>Remote SSH CFT extraction</h2>
                <p>
                    Configure a remote server connection and extract CFT data.
                    This version is static and uses sample data only.
                </p>
            </div>

            <div className="page-content">
                <section className="ssh-form-card">
                    <h3>SSH connection</h3>

                    <form className="ssh-form" onSubmit={handleSubmit}>
                        <div className="form-grid">
                            <label className="form-field">
                                <span>Server host</span>
                                <input
                                    type="text"
                                    name="host"
                                    placeholder="example.server.local"
                                    defaultValue="cft-prod.company.local"
                                />
                            </label>

                            <label className="form-field">
                                <span>Port</span>
                                <input
                                    type="number"
                                    name="port"
                                    placeholder="22"
                                    defaultValue="22"
                                />
                            </label>

                            <label className="form-field">
                                <span>Username</span>
                                <input
                                    type="text"
                                    name="username"
                                    placeholder="ssh user"
                                    defaultValue="cftadmin"
                                />
                            </label>

                            <label className="form-field">
                                <span>Password</span>
                                <input
                                    type="password"
                                    name="password"
                                    placeholder="Password"
                                    defaultValue="password"
                                />
                            </label>

                            <label className="form-field form-field--full">
                                <span>CFT installation path</span>
                                <input
                                    type="text"
                                    name="cftPath"
                                    placeholder="/opt/cft"
                                    defaultValue="/opt/cft"
                                />
                            </label>

                            <label className="form-field form-field--full">
                                <span>Extraction command</span>
                                <input
                                    type="text"
                                    name="command"
                                    placeholder="cftutil list"
                                    defaultValue="cftutil list all"
                                />
                            </label>
                        </div>

                        <div className="form-actions">
                            <Link to="/accueil" className="action-btn action-btn--secondary">
                                Back
                            </Link>

                            <button
                                type="submit"
                                className="action-btn action-btn--primary"
                                disabled={isExtracting}
                            >
                                {isExtracting ? 'Extracting...' : 'Extract CFT data'}
                            </button>
                        </div>
                    </form>
                </section>

                {hasExtracted && (
                    <section className="cft-results-card">
                        <div className="results-header">
                            <div>
                                <h3>Extracted CFT data</h3>
                                <p>
                                    Static sample result from the configured SSH server.
                                </p>
                            </div>

                            <span className="pull-status pull-status--success">
                                Success
                            </span>
                        </div>

                        <div className="cft-table-wrapper">
                            <table className="cft-table">
                                <thead>
                                <tr>
                                    <th>Flow ID</th>
                                    <th>Partner</th>
                                    <th>Direction</th>
                                    <th>File pattern</th>
                                    <th>Status</th>
                                </tr>
                                </thead>
                                <tbody>
                                {mockCftData.map((item) => (
                                    <tr key={item.id}>
                                        <td>{item.id}</td>
                                        <td>{item.partner}</td>
                                        <td>{item.direction}</td>
                                        <td>
                                            <code>{item.filePattern}</code>
                                        </td>
                                        <td>{item.status}</td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>
                    </section>
                )}
            </div>
        </div>
    );
};

export default ServerConfigPage;