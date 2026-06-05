from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


# Project root = parent of the `migration_project/` package.
# Using this absolute anchor keeps the .env discoverable regardless of the
# current working directory (Airflow workers, systemd, cron, etc.).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_env_file() -> None:
    candidates: list[Path] = [_PROJECT_ROOT / ".env"]
    # Path.cwd() can raise FileNotFoundError when the process' working
    # directory has been deleted under it (typical Airflow scenario when
    # the project folder is replaced while the worker is running).
    try:
        candidates.append(Path.cwd() / ".env")
    except (FileNotFoundError, OSError):
        pass

    for env_path in candidates:
        try:
            if not env_path.exists():
                continue
            content = env_path.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            continue
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
        return


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    data_dir: Path
    conf_pattern: str
    airflow_dag_id: str
    cop_db_host: str
    cop_db_port: int
    cop_db_user: str
    cop_db_password: str
    cop_db_name: str
    cop_sync_enabled: bool
    cop_lookback_months: int


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_settings() -> Settings:
    _load_env_file()
    return Settings(
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=int(os.getenv("DB_PORT", "3306")),
        db_user=os.getenv("DB_USER", "root"),
        db_password=os.getenv("DB_PASSWORD", ""),
        db_name=os.getenv("DB_NAME", "migration_db"),
        data_dir=Path(os.getenv("DATA_DIR", os.getenv("CONF_DIR", r"C:\Users\OH\Desktop\data"))),
        conf_pattern=os.getenv("CONF_PATTERN", "conf_cft.*.txt"),
        airflow_dag_id=os.getenv("AIRFLOW_DAG_ID", "cft_daily_import"),
        cop_db_host=os.getenv("COP_DB_HOST", ""),
        cop_db_port=int(os.getenv("COP_DB_PORT", "3306")),
        cop_db_user=os.getenv("COP_DB_USER", ""),
        cop_db_password=os.getenv("COP_DB_PASSWORD", ""),
        cop_db_name=os.getenv("COP_DB_NAME", "copilote"),
        cop_sync_enabled=_to_bool(os.getenv("COP_SYNC_ENABLED", "false")),
        cop_lookback_months=int(os.getenv("COP_LOOKBACK_MONTHS", "1")),
    )
