import { useState, useMemo } from 'react';
import { DatabaseTable } from '../../services/databaseService';
import './database.css';

interface DataTableProps {
    table: DatabaseTable;
}

const PAGE_SIZES = [10, 25, 50];

function DataTable({ table }: DataTableProps) {
    const [search, setSearch] = useState('');
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [sortCol, setSortCol] = useState<string | null>(null);
    const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

    // ── Filter rows by search ────────────────────────────────────────────
    const filteredRows = useMemo(() => {
        if (!search.trim()) return table.rows;
        const q = search.toLowerCase();
        return table.rows.filter((row) =>
            table.columns.some((col) => {
                const val = row[col.name];
                return val !== null && val !== undefined && String(val).toLowerCase().includes(q);
            }),
        );
    }, [table.rows, table.columns, search]);

    // ── Sort rows ────────────────────────────────────────────────────────
    const sortedRows = useMemo(() => {
        if (!sortCol) return filteredRows;
        return [...filteredRows].sort((a, b) => {
            const av = a[sortCol] ?? '';
            const bv = b[sortCol] ?? '';
            const aStr = String(av);
            const bStr = String(bv);
            // Try numeric comparison
            const aNum = Number(av);
            const bNum = Number(bv);
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return sortDir === 'asc' ? aNum - bNum : bNum - aNum;
            }
            return sortDir === 'asc'
                ? aStr.localeCompare(bStr)
                : bStr.localeCompare(aStr);
        });
    }, [filteredRows, sortCol, sortDir]);

    // ── Paginate ─────────────────────────────────────────────────────────
    const totalPages = Math.max(1, Math.ceil(sortedRows.length / pageSize));
    const safePage = Math.min(page, totalPages);
    const pagedRows = sortedRows.slice((safePage - 1) * pageSize, safePage * pageSize);

    const isEmpty = table.rows.length === 0;
    const isFiltered = search.trim().length > 0;

    const handleSort = (colName: string) => {
        if (sortCol === colName) {
            setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
        } else {
            setSortCol(colName);
            setSortDir('asc');
        }
        setPage(1);
    };

    const handleSearchChange = (val: string) => {
        setSearch(val);
        setPage(1);
    };

    const handlePageSizeChange = (size: number) => {
        setPageSize(size);
        setPage(1);
    };

    // Page range for pagination buttons
    const getPageRange = (): number[] => {
        const range: number[] = [];
        const maxButtons = 7;
        if (totalPages <= maxButtons) {
            for (let i = 1; i <= totalPages; i++) range.push(i);
        } else {
            range.push(1);
            let start = Math.max(2, safePage - 1);
            let end = Math.min(totalPages - 1, safePage + 1);
            if (safePage <= 3) { start = 2; end = 5; }
            if (safePage >= totalPages - 2) { start = totalPages - 4; end = totalPages - 1; }
            if (start > 2) range.push(-1); // ellipsis
            for (let i = start; i <= end; i++) range.push(i);
            if (end < totalPages - 1) range.push(-2); // ellipsis
            range.push(totalPages);
        }
        return range;
    };

    return (
        <div className="data-table">
            {/* ── Header bar ──────────────────────────────────── */}
            <div className="data-table-topbar">
                <div className="data-table-title-area">
                    <h3>{table.name}</h3>
                    <span className="row-count">
                        {isEmpty
                            ? 'Aucun enregistrement'
                            : isFiltered
                                ? `${filteredRows.length} sur ${table.rows.length} enregistrements`
                                : `${table.rows.length} enregistrements`}
                    </span>
                </div>
                <div className="data-table-search">
                    <svg className="search-icon" viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                        <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                    </svg>
                    <input
                        type="text"
                        placeholder="Rechercher dans tous les champs…"
                        value={search}
                        onChange={(e) => handleSearchChange(e.target.value)}
                    />
                    {search && (
                        <button
                            type="button"
                            className="search-clear"
                            onClick={() => handleSearchChange('')}
                        >
                            ✕
                        </button>
                    )}
                </div>
            </div>

            <p className="data-table-description">{table.description}</p>

            {/* ── Table ───────────────────────────────────────── */}
            <div className="table-wrapper">
                <table>
                    <thead>
                    <tr>
                        {table.columns.map((col) => (
                            <th
                                key={col.name}
                                onClick={() => handleSort(col.name)}
                                className={sortCol === col.name ? 'sorted' : ''}
                            >
                                <span className="th-content">
                                    {col.name}
                                    {sortCol === col.name && (
                                        <span className="sort-arrow">
                                            {sortDir === 'asc' ? '↑' : '↓'}
                                        </span>
                                    )}
                                </span>
                                <span className="column-type">{col.type}</span>
                            </th>
                        ))}
                    </tr>
                    </thead>
                    <tbody>
                    {pagedRows.length === 0 ? (
                        <tr>
                            <td colSpan={table.columns.length} className="empty-state">
                                {isFiltered
                                    ? `Aucun résultat pour « ${search} »`
                                    : 'Aucune donnée — connectez le serveur et lancez l\'extraction CFT'}
                            </td>
                        </tr>
                    ) : (
                        pagedRows.map((row, index) => (
                            <tr key={index}>
                                {table.columns.map((col) => {
                                    const val = row[col.name];
                                    let display = val === null || val === undefined ? '—' : String(val);
                                    // Truncate long values
                                    if (display.length > 80) display = display.slice(0, 77) + '…';
                                    // Style booleans
                                    const isBool = col.type === 'boolean';
                                    return (
                                        <td key={col.name} title={String(val ?? '')}>
                                            {isBool ? (
                                                <span className={`bool-badge ${val ? 'bool-true' : 'bool-false'}`}>
                                                    {val ? 'oui' : 'non'}
                                                </span>
                                            ) : (
                                                display
                                            )}
                                        </td>
                                    );
                                })}
                            </tr>
                        ))
                    )}
                    </tbody>
                </table>
            </div>

            {/* ── Pagination ──────────────────────────────────── */}
            {sortedRows.length > 0 && (
                <div className="pagination-bar">
                    <div className="page-size-selector">
                        <span>Lignes :</span>
                        {PAGE_SIZES.map((size) => (
                            <button
                                key={size}
                                type="button"
                                className={pageSize === size ? 'ps-btn active' : 'ps-btn'}
                                onClick={() => handlePageSizeChange(size)}
                            >
                                {size}
                            </button>
                        ))}
                    </div>

                    <div className="page-info">
                        {(safePage - 1) * pageSize + 1}–{Math.min(safePage * pageSize, sortedRows.length)} sur {sortedRows.length}
                    </div>

                    <div className="page-buttons">
                        <button
                            type="button"
                            className="pg-btn"
                            disabled={safePage <= 1}
                            onClick={() => setPage(1)}
                            title="Première page"
                        >
                            «
                        </button>
                        <button
                            type="button"
                            className="pg-btn"
                            disabled={safePage <= 1}
                            onClick={() => setPage(safePage - 1)}
                            title="Page précédente"
                        >
                            ‹
                        </button>
                        {getPageRange().map((p, i) =>
                            p < 0 ? (
                                <span key={`e${i}`} className="pg-ellipsis">…</span>
                            ) : (
                                <button
                                    key={p}
                                    type="button"
                                    className={p === safePage ? 'pg-btn active' : 'pg-btn'}
                                    onClick={() => setPage(p)}
                                >
                                    {p}
                                </button>
                            ),
                        )}
                        <button
                            type="button"
                            className="pg-btn"
                            disabled={safePage >= totalPages}
                            onClick={() => setPage(safePage + 1)}
                            title="Page suivante"
                        >
                            ›
                        </button>
                        <button
                            type="button"
                            className="pg-btn"
                            disabled={safePage >= totalPages}
                            onClick={() => setPage(totalPages)}
                            title="Dernière page"
                        >
                            »
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default DataTable;