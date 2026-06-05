import { Link } from 'react-router-dom';
import './LandingPage.css';

function LandingPage() {
    return (
        <div className="landing-page">
            <section className="hero">
                <h2>Plateforme de migration CFT vers B2Bi</h2>
                <p className="hero-description">
                    Inventorier, transformer et déployer les configurations de transfert de fichiers d'Axway CFT vers Axway B2Bi via un pipeline structuré et auditable.
                </p>
                <Link to="/server-config" className="cta-button">
                    Commencer
                </Link>
            </section>

            <section className="phases">
                <div className="phase-card">
                    <div className="phase-number">1</div>
                    <h3>Inventaire</h3>
                    <p>Analyser les exportations CFTUTIL et les configurations Bosco dans une base de données interrogeable.</p>
                </div>
                <div className="phase-card">
                    <div className="phase-number">2</div>
                    <h3>Generer</h3>
                    <p>Transformer les configurations CFT en objets B2Bi grâce à un moteur de règles.</p>
                </div>
                <div className="phase-card">
                    <div className="phase-number">3</div>
                    <h3>Déployer</h3>
                    <p>Transmettez les configurations à B2Bi via l'API REST et validez-les de bout en bout.</p>
                </div>
            </section>
        </div>
    );
}

export default LandingPage;