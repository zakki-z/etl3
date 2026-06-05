# migration_projet — Inventaire CFT (SQLAlchemy + Airflow)

Pipeline d’ingestion des configurations et de la supervision CFT vers une base MySQL, en préparation de la migration des flux vers **Axway B2Bi**.

## Rôle du projet

Le pipeline collecte et structure les données issues de plusieurs sources, puis les charge dans une base d’inventaire :

| Étape | Source | Tables principales |
|-------|--------|-------------------|
| Configuration CFT | Exports `conf_cft.*.txt` | `cft_partner`, `cft_tcp`, `cft_flow` |
| Supervision | Copilote (`flux`) | `transfer` |
| Post-traitement | Scripts `.bat` | `post_processing_scripts`, `flow_action` |
| Applicatif | MonCFT (`.ini`) | `moncft_config` |
| Applicatif | BoscoSend (`configuration.ini`) | `boscosend_config` |

### Détail import configuration CFT

Depuis les blocs d’export :

- `cft_partner` ← `CFTPART`
- `cft_tcp` ← `CFTTCP` (rattaché au partenaire via le même `ID` que `CFTPART`)
- `cft_flow` ← `CFTSEND` et `CFTRECV` avec :
  - `direct = 'send'` pour `CFTSEND`
  - `direct = 'recv'` pour `CFTRECV`

Les enregistrements `CFTTCP` sans partenaire correspondant ne sont pas perdus : ils sont stockés dans `stg_cft_tcp_without_partner` (consultables via la vue `v_stg_cft_tcp_without_partner`).

## Prérequis

- Python 3.12+
- MySQL 8.x
- Apache Airflow 3.x (pour l’orchestration planifiée)

## Installation

1. Créer un environnement virtuel :

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux
# .venv\Scripts\activate    # Windows
```

2. Installer les dépendances :

```bash
pip install -r requirements.txt
```

3. Créer un fichier `.env` à la racine du projet (non versionné) et renseigner les variables :

- connexion MySQL inventaire (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`)
- `DATA_DIR` : racine des données (`conf`, `scripts`, `moncft`, `boscosend` par serveur)
- Copilote (optionnel) : `COP_SYNC_ENABLED`, `COP_DB_*`, `COP_LOOKBACK_MONTHS`
- `AIRFLOW_DAG_ID` (par défaut : `cft_daily_import`)

## Exécution locale

Lancer toute la chaîne d’import :

```bash
python main.py
```

Ordre des traitements : conf CFT → Copilote → scripts post-transfert → MonCFT → BoscoSend.

## Base de données — contrainte `cft_flow`

Le code effectue des upserts sur `cft_flow` avec `ON DUPLICATE KEY UPDATE` sur la clé :

- `(idf_code, direct)`

Si l’index unique n’existe pas encore, l’exécuter une fois (adapter le nom de schéma) :

```sql
ALTER TABLE pfe_migration.cft_flow
ADD UNIQUE KEY uq_cft_flow_idf_direct (idf_code, direct);
```

Scripts SQL fournis dans `sql/` :

- `001_constraints.sql`
- `002_conf_id_primary_keys.sql` (clés primaires basées sur les ID conf)
- scripts de migration suivants (`003` à `009`)

## Airflow

Le DAG `dags/cft_import_dag.py` enchaîne les mêmes traitements que `main.py`, planifié chaque jour à **03:00** (fuseau `Europe/Paris`), avec reprise automatique en cas d’échec.

Configurer le `dags_folder` Airflow vers le répertoire `dags/` de ce projet (ou copier le fichier DAG).

Le DAG ajoute la racine du dépôt à `sys.path` pour les imports Python.

## Notes techniques

- Colonne `cft_tcp.cnxout` : valeur issue du champ conf `CNXOUT`.
- Parsing des exports en **streaming** (ligne par ligne) pour les gros fichiers de configuration.
- Ne jamais committer `.env` ni le dossier `.venv/`.

## Structure du dépôt

```text
main.py                 # point d’entrée pipeline
migration_project/      # parsers, services, modèles, repositories
dags/                   # DAG Airflow
sql/                    # scripts de schéma et contraintes
requirements.txt
```
