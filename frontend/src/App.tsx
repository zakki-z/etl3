import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layout/main/MainLayout';
import LandingPage from './pages/landingPage/LandingPage';
import ServerConfigPage from './pages/serverConfig/ServerConfigPage';
import DatabasePage from './pages/database/databasepage';
import DashboardPage from './pages/dashboard/dashboardPage';
import B2biConfigPage from './pages/b2biConfig/B2biConfigPage';
import './App.css';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Navigate to="/accueil" replace />} />
                <Route path="/accueil" element={<MainLayout><LandingPage /></MainLayout>} />
                <Route path="/server-config" element={<MainLayout><ServerConfigPage /></MainLayout>} />
                <Route path="/database" element={<MainLayout><DatabasePage /></MainLayout>} />
                <Route path="/dashboard" element={<MainLayout><DashboardPage /></MainLayout>} />
                <Route path="/b2bi" element={<MainLayout><B2biConfigPage /></MainLayout>} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;