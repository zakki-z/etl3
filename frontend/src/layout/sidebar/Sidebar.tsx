import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useMsal } from '@azure/msal-react';
import './Sidebar.css';

function getInitials(name?: string): string {
    if (!name) {
        return '?';
    }

    return name
        .split(' ')
        .map((part) => part[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
}

function Sidebar() {
    const location = useLocation();
    const { instance, accounts } = useMsal();
    const [isCollapsed, setIsCollapsed] = useState(false);
    const user = accounts[0];

    const handleLogout = () => {
        instance.logoutRedirect({
            postLogoutRedirectUri: '/',
        }).catch(console.error);
    };

    return (
        <aside className={isCollapsed ? 'sidebar collapsed' : 'sidebar'}>
            <button
                type="button"
                className="sidebar-toggle"
                onClick={() => setIsCollapsed((current) => !current)}
                aria-label={isCollapsed ? 'Open sidebar' : 'Close sidebar'}
            >
                {isCollapsed ? '☰' : '×'}
            </button>

            <div className="sidebar-brand">
                {!isCollapsed && <span>Stroom</span>}
                {!isCollapsed && <small>CFT → B2Bi Migration</small>}
            </div>

            <nav className="sidebar-nav">
                <Link
                    to="/accueil"
                    className={location.pathname === '/accueil' ? 'sidebar-link active' : 'sidebar-link'}
                    title="Config de serveur"
                >
                    <span className="sidebar-icon">⌂</span>
                    {!isCollapsed && <span>accueil</span>}
                </Link>
                <Link
                    to="/dashboard"
                    className={location.pathname === '/dashboard' ? 'sidebar-link active' : 'sidebar-link'}
                    title="dashboard"
                >
                    <span className="sidebar-icon">📊</span>
                    {!isCollapsed && <span>Dashboard</span>}
                </Link>
                <Link
                    to="/server-config"
                    className={location.pathname === '/server-config' ? 'sidebar-link active' : 'sidebar-link'}
                    title="Config de serveur"
                >
                    <span className="sidebar-icon">⚙</span>
                    {!isCollapsed && <span>Config de serveur</span>}
                </Link>

                <Link
                    to="/database"
                    className={location.pathname === '/database' ? 'sidebar-link active' : 'sidebar-link'}
                    title="Base de données"
                >
                    <span className="sidebar-icon">🛢</span>
                    {!isCollapsed && <span>Base de données</span>}
                </Link>
                <Link
                    to="/b2bi"
                    className={location.pathname === '/b2bi' ? 'sidebar-link active' : 'sidebar-link'}
                    title="B2BI config"
                >
                    <span className="sidebar-icon"> 🛠</span>
                    {!isCollapsed && <span>B2BI config</span>}
                </Link>
            </nav>

            <div className="sidebar-account">
                <div className="account-avatar">
                    {getInitials(user?.name)}
                </div>

                {!isCollapsed && (
                    <>
                        <div className="account-meta">
                            <span className="account-name">{user?.name || 'Guest'}</span>
                            <span className="account-email">{user?.username || 'Not signed in'}</span>
                        </div>

                        {user && (
                            <button type="button" className="logout-button" onClick={handleLogout}>
                                Sign out
                            </button>
                        )}
                    </>
                )}
            </div>
        </aside>
    );
}

export default Sidebar;