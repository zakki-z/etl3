"""
Shared pytest fixtures for the Stroom test suite.

Uses SQLite in-memory — no MySQL required in CI.
All tables are created via raw DDL (no ORM metadata) to avoid FK resolution
order issues between models.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

SQLITE_URL = "sqlite://"

_DDL = """
CREATE TABLE IF NOT EXISTS server (
    id          VARCHAR(19) PRIMARY KEY,
    host        VARCHAR(255),
    environment VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS cft_partner (
    id      VARCHAR(100) PRIMARY KEY,
    nspart  VARCHAR(100),
    nrpart  VARCHAR(100),
    ipart   VARCHAR(100),
    ssl     TINYINT,
    sap     VARCHAR(100),
    nspassw VARCHAR(100),
    nrpassw VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS cft_tcp (
    partner_id VARCHAR(100) PRIMARY KEY,
    cnxout     VARCHAR(100),
    host       VARCHAR(100),
    FOREIGN KEY (partner_id) REFERENCES cft_partner(id)
);

CREATE TABLE IF NOT EXISTS cft_flow (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    idf_code VARCHAR(100) NOT NULL,
    direct   VARCHAR(100) NOT NULL,
    fcode    VARCHAR(100),
    ftype    VARCHAR(100),
    flrecl   VARCHAR(100),
    frecfm   VARCHAR(100),
    fname    VARCHAR(100),
    xlate    TINYINT,
    exec     VARCHAR(1000),
    exece    VARCHAR(1000),
    UNIQUE (idf_code, direct)
);

CREATE TABLE IF NOT EXISTS transfer (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id VARCHAR(19),
    idf_id     INTEGER,
    date       DATE,
    direct     VARCHAR(100),
    server_id  VARCHAR(19),
    statut     VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS post_processing_scripts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id   VARCHAR(19) NOT NULL,
    script_path VARCHAR(500) NOT NULL,
    script_name VARCHAR(255) NOT NULL,
    UNIQUE (server_id, script_path)
);

CREATE TABLE IF NOT EXISTS flow_action (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id    INTEGER NOT NULL,
    scope_type   VARCHAR(20) NOT NULL,
    idf_id       INTEGER,
    partner_id   VARCHAR(19),
    ipart_value  VARCHAR(255),
    action_order INTEGER NOT NULL DEFAULT 0,
    action_text  VARCHAR(2000) NOT NULL
);

CREATE TABLE IF NOT EXISTS moncft_config (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_id INTEGER,
    fname       VARCHAR(500),
    filtre      VARCHAR(255),
    parm        VARCHAR(255),
    nfname      VARCHAR(255),
    sappl       VARCHAR(100),
    rappl       VARCHAR(100),
    suser       VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS boscosend_config (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    remote_address   VARCHAR(100),
    remote_subdir    VARCHAR(500),
    transfer_id      INTEGER,
    localdir         VARCHAR(500),
    backup_dir       VARCHAR(500),
    file_search_mask VARCHAR(500),
    nom_section      VARCHAR(255),
    "Cmdb-Prestation" VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS stg_cft_tcp_without_partner (
    id     VARCHAR(100) PRIMARY KEY,
    cnxout VARCHAR(100),
    host   VARCHAR(100),
    reason VARCHAR(255)
);
"""


@pytest.fixture(scope="function")
def engine():
    eng = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    with eng.begin() as conn:
        for stmt in _DDL.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
    yield eng
    eng.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def seed_partner(session: Session, conf_id: str = "PART01", **kw) -> None:
    session.execute(text(
        "INSERT INTO cft_partner (id, nspart, nrpart, ipart, ssl, sap) "
        "VALUES (:id,:nspart,:nrpart,:ipart,:ssl,:sap)"
    ), {
        "id":     conf_id,
        "nspart": kw.get("nspart", "NS_" + conf_id),
        "nrpart": kw.get("nrpart", "NR_" + conf_id),
        "ipart":  kw.get("ipart", None),
        "ssl":    kw.get("ssl", 0),
        "sap":    kw.get("sap", "0"),
    })


def seed_flow(session: Session, idf_code: str = "IDF01",
              direct: str = "send", **kw) -> int:
    session.execute(text(
        "INSERT INTO cft_flow (idf_code, direct, fcode, ftype, xlate) "
        "VALUES (:c,:d,:fc,:ft,:xl)"
    ), {
        "c":  idf_code, "d": direct,
        "fc": kw.get("fcode", "BINARY"),
        "ft": kw.get("ftype", "B"),
        "xl": kw.get("xlate", 0),
    })
    return session.execute(
        text("SELECT id FROM cft_flow WHERE idf_code=:c AND direct=:d"),
        {"c": idf_code, "d": direct}
    ).first()[0]


def seed_server(session: Session, server_id: str = "SRV01") -> None:
    session.execute(text(
        "INSERT OR IGNORE INTO server (id, host, environment) "
        "VALUES (:id,:host,:env)"
    ), {"id": server_id, "host": "srv.local", "env": "prod"})


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def api_client(engine, db_session):
    from app import app
    from migration_project.routers import deps

    app.dependency_overrides[deps.get_db] = lambda: (yield db_session)
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_conf_dir(tmp_path: Path) -> Path:
    return tmp_path


def write_conf(path: Path, content: str) -> Path:
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path