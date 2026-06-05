import { useState } from 'react';
import { InteractionStatus } from '@azure/msal-browser';
import { useIsAuthenticated, useMsal } from '@azure/msal-react';
import { loginRequest } from '../../auth/authConfig';
import './login.css';
import {Navigate} from "react-router-dom";


function LoginPage() {
    const { instance, inProgress } = useMsal();
    const [loading, setLoading] = useState(false);

    const handleLogin = async () => {
        if (inProgress !== InteractionStatus.None) {
            return;
        }

        setLoading(true);

        try {
            await instance.loginRedirect(loginRequest);
        } catch (e) {
            console.error(e);
            setLoading(false);
        }
    };

    return (
        <div className="login-page">
            <section className="login-card" aria-labelledby="login-title">
                <div className="login-card__header">
                    <div className="login-logo" aria-hidden="true">
                        S
                    </div>
                    <h2 id="login-title">Connexion à Stroom</h2>
                    <p>
                        Connectez-vous avec votre compte Microsoft pour accéder à la
                        plateforme de migration et poursuivre votre travail.
                    </p>
                </div>

                <button
                    type="button"
                    className="login-button login-button--microsoft"
                    onClick={handleLogin}
                    disabled={loading || inProgress !== InteractionStatus.None}
                >
                    <svg
                        width="20"
                        height="20"
                        viewBox="0 0 21 21"
                        xmlns="http://www.w3.org/2000/svg"
                        aria-hidden="true"
                    >
                        <rect x="1" y="1" width="9" height="9" fill="#f25022" />
                        <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
                        <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
                        <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
                    </svg>
                    {loading ? 'Connexion...' : 'Se connecter avec Microsoft'}
                </button>

                <div className="login-hint">
                    Vous serez redirigé vers Microsoft pour sécuriser votre session.
                </div>
            </section>
        </div>
    );
}

function Dashboard() {
    return <Navigate to="/accueil" replace />;
}
export default function Login() {
    const isAuthenticated = useIsAuthenticated();
    return isAuthenticated ? <Dashboard /> : <LoginPage />;
}