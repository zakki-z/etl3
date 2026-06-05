import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { InteractionStatus } from '@azure/msal-browser';
import { useIsAuthenticated, useMsal } from '@azure/msal-react';

interface ProtectedRouteProps {
    children: ReactNode;
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
    const isAuthenticated = useIsAuthenticated();
    const { inProgress } = useMsal();
    const location = useLocation();

    if (inProgress !== InteractionStatus.None) {
        return null;
    }

    if (!isAuthenticated) {
        return <Navigate to="/" replace state={{ from: location }} />;
    }

    return <>{children}</>;
}

export default ProtectedRoute;