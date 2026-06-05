from __future__ import annotations


from datetime import datetime, timedelta
import sys
from pathlib import Path
from zoneinfo import ZoneInfo


from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator


_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


from main import (
    run_boscosend_import,
    run_conf_import,
    run_copilot_sync,
    run_moncft_import,
    run_post_scripts_import,
)
from migration_project.config import get_settings




settings = get_settings()


PARIS_TZ = ZoneInfo("Europe/Paris")


with DAG(
    dag_id=settings.airflow_dag_id,
    start_date=datetime(2026, 1, 1, tzinfo=PARIS_TZ),
    schedule="0 3 * * *",
    catchup=False,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=10),
    },
    tags=["cft", "mysql", "migration"],
) as dag:
    parse_and_import_conf = PythonOperator(
        task_id="parse_and_import_conf",
        python_callable=run_conf_import,
    )


    sync_copilot_transfers = PythonOperator(
        task_id="sync_copilot_transfers",
        python_callable=run_copilot_sync,
    )


    parse_post_transfer_scripts = PythonOperator(
        task_id="parse_post_transfer_scripts",
        python_callable=run_post_scripts_import,
    )


    parse_moncft_config = PythonOperator(
        task_id="parse_moncft_config",
        python_callable=run_moncft_import,
    )


    parse_boscosend_config = PythonOperator(
        task_id="parse_boscosend_config",
        python_callable=run_boscosend_import,
    )


    (
        parse_and_import_conf
        >> sync_copilot_transfers
        >> parse_post_transfer_scripts
        >> parse_moncft_config
        >> parse_boscosend_config
    )


