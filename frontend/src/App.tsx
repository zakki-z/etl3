import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './layout/main/MainLayout';
import LandingPage from './pages/landingPage/LandingPage';
import ServerConfigPage from './pages/serverConfig/ServerConfigPage';
import DatabasePage from './pages/database/databasepage';
import Login from './pages/auth/login';
import './App.css';
import DashboardPage from "./pages/dashboard/dashboardPage";
import B2biConfigPage from "./pages/b2biConfig/B2biConfigPage";
import ProtectedRoute from "./auth/ProtectedRoute";

function App() {
  return (
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route
              path="/accueil"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <LandingPage />
                  </MainLayout>
                </ProtectedRoute>
              }
          />

          <Route
              path="/server-config"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <ServerConfigPage />
                  </MainLayout>
                </ProtectedRoute>
              }
          />

          <Route
              path="/database"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <DatabasePage />
                  </MainLayout>
                </ProtectedRoute>
              }
          />
          <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <DashboardPage />
                  </MainLayout>
                </ProtectedRoute>
              }
          />
          <Route
              path="/b2bi"
              element={
                <ProtectedRoute>
                  <MainLayout>
                    <B2biConfigPage />
                  </MainLayout>
                </ProtectedRoute>
              }
          />
        </Routes>
      </BrowserRouter>
  );
}

export default App;