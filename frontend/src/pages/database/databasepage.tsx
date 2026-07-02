import { useState, useEffect, useCallback } from 'react';
import DataTable from '../../components/database/database';
import { tableDefinitions, DatabaseTable, fetchTableRows, downloadTableAsJson } from '../../services/databaseService';
import './databasepage.css';

function DatabasePage() {
    const [selectedTable, setSelectedTable] = useState<string>(tableDefinitions[0].name);
    const [currentTable, setCurrentTable] = useState<DatabaseTable | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadTable = useCallback(async () => {
        const def = tableDefinitions.find((table) => table.name === selectedTable);
        if (!def) return;

        setLoading(true);
        setError(null);

        try {
            const rows = await fetchTableRows(selectedTable);
            setCurrentTable({ ...def, rows });
        } catch (e: any) {
            setError(e.message || 'Erreur de chargement');
            setCurrentTable({ ...def, rows: [] });
        } finally {
            setLoading(false);
        }
    }, [selectedTable]);

    useEffect(() => {
        loadTable();
    }, [loadTable]);

    return (
        <div className="database-page">
            <div className="page-header">
                <h2>Base de données</h2>
                <p>Consultez les tableaux d'inventaire extraits de la plateforme CFT.</p>
            </div>

            <div className="database-layout">
                <aside className="table-sidebar">
                    <h3>Tables</h3>
                    <ul className="table-list">
                        {tableDefinitions.map((table) => (
                            <li key={table.name}>
                                <button
                                    type="button"
                                    className={selectedTable === table.name ? 'table-item active' : 'table-item'}
                                    onClick={() => setSelectedTable(table.name)}
                                >
                                    {table.name}
                                </button>
                            </li>
                        ))}
                    </ul>
                </aside>

                <section className="table-viewer">
                    {error && (
                        <div className="error-banner">
                            <span>⚠</span> {error}
                            <button type="button" onClick={loadTable} className="retry-btn">
                                Réessayer
                            </button>
                        </div>
                    )}

                    {currentTable && !loading && (
                        <div className="table-toolbar">
                            <button
                                type="button"
                                className="download-btn"
                                onClick={() => downloadTableAsJson(currentTable)}
                                disabled={currentTable.rows.length === 0}
                            >
                                ⬇ Télécharger JSON
                            </button>
                        </div>
                    )}

                    {loading && <div className="loading-indicator">Chargement…</div>}

                    {currentTable && !loading && <DataTable table={currentTable} />}
                </section>
            </div>
        </div>
    );
}

export default DatabasePage;