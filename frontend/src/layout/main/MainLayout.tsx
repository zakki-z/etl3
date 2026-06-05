import { ReactNode } from 'react';
import Sidebar from '../sidebar/Sidebar';
import './MainLayout.css';

interface MainLayoutProps {
    children: ReactNode;
}

function MainLayout({ children }: MainLayoutProps) {
    return (
        <div className="main-layout">
            <Sidebar />

            <div className="main-panel">
                <main className="main-content">{children}</main>
            </div>
        </div>
    );
}

export default MainLayout;