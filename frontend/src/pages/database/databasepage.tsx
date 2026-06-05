import { useState, useEffect, useCallback } from 'react';
import { useMsal } from '@azure/msal-react';
import DataTable from '../../components/database/database';
import { tableDefinitions, DatabaseTable } from '../../services/databaseService';
import {
    fetchBoscoSendConfig,
    fetchCFTConfig,
    fetchCFTFlows,
    fetchCFTPartners,
    fetchCFTTCP,
    fetchCFTWithoutPartner,
    fetchFlowActions,
    fetchPostProcessingScripts,
    fetchServers,
    fetchTransfers,
} from '../../services/api';
import './databasepage.css';

function toTableRows<T extends object>(rows: T[]): Record<string, unknown>[] {
    return rows.map((row) => Object.assign({}, row) as Record<string, unknown>);
}

function DatabasePage() {
    const { instance } = useMsal();
    const [selectedTable, setSelectedTable] = useState<string>(tableDefinitions[0].name);
    const [currentTable, setCurrentTable] = useState<DatabaseTable | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchRowsByTableName = useCallback(async (tableName: string): Promise<Record<string, unknown>[]> => {
        switch (tableName) {
            case 'server':
                return toTableRows(await fetchServers(instance));

            case 'cft_partner':
                return toTableRows(await fetchCFTPartners(instance));

            case 'cft_flow':
                return toTableRows(await fetchCFTFlows(instance));

            case 'cft_tcp':
                return toTableRows(await fetchCFTTCP(instance));

            case 'transfer':
                return toTableRows(await fetchTransfers(instance));

            case 'flow_action':
                return toTableRows(await fetchFlowActions(instance));

            case 'post_processing_scripts':
                return toTableRows(await fetchPostProcessingScripts(instance));

            case 'moncft_config':
                return toTableRows(await fetchCFTConfig(instance));

            case 'boscosend_config':
                return toTableRows(await fetchBoscoSendConfig(instance));

            case 'cft_tcp_without_partner':
                return toTableRows(await fetchCFTWithoutPartner(instance));

            default:
                return [];
        }
    }, [instance]);

    const loadTable = useCallback(async () => {
        const def = tableDefinitions.find((table) => table.name === selectedTable);
        if (!def) return;

        setLoading(true);
        setError(null);

        try {
            const rows = await fetchRowsByTableName(selectedTable);
            setCurrentTable({ ...def, rows });
        } catch (e: any) {
            setError(e.message || 'Erreur de chargement');
            setCurrentTable({ ...def, rows: [] });
        } finally {
            setLoading(false);
        }
    }, [selectedTable, fetchRowsByTableName]);

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

                    {loading && <div className="loading-indicator">Chargement…</div>}

                    {currentTable && !loading && <DataTable table={currentTable} />}
                </section>
            </div>
        </div>
    );
}

export default DatabasePage;