from __future__ import annotations

from migration_project.config import get_settings
from migration_project.db import init_database
from migration_project.db import session_scope
from migration_project.services.boscosend_import import BoscoSendImportService
from migration_project.services.copilot_sync import CopilotSyncService
from migration_project.services.import_service import ImportService
from migration_project.services.moncft_import import MonCftImportService
from migration_project.services.post_script_import import PostScriptImportService
from migration_project.utils.file_selector import get_matching_server_conf_files


def run_conf_import() -> None:
    """Parse les fichiers de conf de chaque serveur et upsert cft_partner / cft_tcp / cft_flow."""
    settings = get_settings()
    init_database()
    conf_files = get_matching_server_conf_files(settings.data_dir, settings.conf_pattern)
    report = ImportService().run_many(conf_files)

    print(f"Files processed: {report.files_processed}")
    print(f"File range: {report.file_path}")
    print(f"CFTPART parsed: {report.partner_parsed}")
    print(f"cft_partner upserted: {report.partner_upserted}")
    print(f"CFTTCP parsed: {report.tcp_parsed}")
    print(f"cft_tcp upserted: {report.tcp_upserted}")
    print(f"cft_tcp missing partner: {report.tcp_missing_partner}")
    print(f"cft_tcp staged (without partner): {report.tcp_staged_missing}")
    print(f"CFTSEND parsed: {report.send_parsed}")
    print(f"CFTRECV parsed: {report.recv_parsed}")
    print(f"cft_flow upserted: {report.flow_upserted}")


def run_copilot_sync() -> None:
    """Recharge transfer depuis copilote.flux sur la fenêtre COP_LOOKBACK_MONTHS (si activé)."""
    settings = get_settings()
    if not settings.cop_sync_enabled:
        print("Copilot sync disabled (COP_SYNC_ENABLED=false). Skipping.")
        return

    with session_scope() as session:
        copilot_report = CopilotSyncService().run(session)
    print(f"transfer deleted before Copilot reload: {copilot_report.transfers_deleted}")
    print(f"transfer inserted from Copilot: {copilot_report.transfers_inserted}")
    print(f"transfer skipped rows from Copilot: {copilot_report.skipped_flux_rows}")


def run_post_scripts_import() -> None:
    """Parse les scripts post-transfert (RECV*.bat / SEND*.bat) sous data/<server>/scripts/."""
    with session_scope() as session:
        report = PostScriptImportService().run(session)

    print(f"post-scripts servers scanned: {report.servers_scanned}")
    print(f"post-scripts files seen: {report.scripts_seen}")
    print(f"post-scripts global imported: {report.global_scripts_imported}")
    print(f"post-scripts specific imported: {report.specific_scripts_imported}")
    print(f"flow_action rows inserted: {report.actions_inserted}")
    print(f"actions skipped (unknown idf): {report.skipped_unknown_idf}")
    print(f"actions skipped (unknown partner): {report.skipped_unknown_partner}")
    print(f"specific scripts skipped (not in cft_flow.exec/exece): {report.skipped_specific_unbound}")
    if report.missing_servers:
        print(f"server folders ignored (not in server table): {report.missing_servers}")


def run_moncft_import() -> None:
    """Parse les fichiers C2I_MonCft<XXX>.ini sous data/<server>/moncft/."""
    with session_scope() as session:
        report = MonCftImportService().run(session)

    print(f"moncft servers scanned: {report.servers_scanned}")
    print(f"moncft files seen: {report.files_seen}")
    print(f"moncft files skipped (copy): {report.files_skipped_copy}")
    print(f"moncft sections parsed: {report.sections_parsed}")
    print(f"moncft inserted with transfer: {report.inserted_with_transfer}")
    print(f"moncft inserted without transfer (NULL): {report.inserted_without_transfer}")
    print(f"moncft skipped (unknown idf): {report.skipped_unknown_idf}")
    print(f"moncft skipped (unknown partner): {report.skipped_unknown_partner}")
    if report.missing_servers:
        print(f"server folders ignored (not in server table): {report.missing_servers}")


def run_boscosend_import() -> None:
    """Parse les fichiers Bosco SEND sous data/<server>/boscosend/configuration.ini."""
    with session_scope() as session:
        report = BoscoSendImportService().run(session)

    print(f"boscosend servers scanned: {report.servers_scanned}")
    print(f"boscosend files seen: {report.files_seen}")
    print(f"boscosend sections parsed: {report.sections_parsed}")
    print(f"boscosend inserted with transfer: {report.inserted_with_transfer}")
    print(f"boscosend inserted without transfer (NULL): {report.inserted_without_transfer}")
    print(f"boscosend missing cft mapping: {report.missing_cft_mapping}")
    print(f"boscosend unknown idf: {report.unknown_idf}")
    print(f"boscosend unknown partner: {report.unknown_partner}")
    print(f"boscosend missing transfer: {report.missing_transfer}")
    if report.missing_servers:
        print(f"server folders ignored (not in server table): {report.missing_servers}")


def run_pipeline() -> None:
    """Lance toute la chaîne en une seule fois (utile en local : `python main.py`)."""
    run_conf_import()
    run_copilot_sync()
    run_post_scripts_import()
    run_moncft_import()
    run_boscosend_import()


if __name__ == "__main__":
    run_pipeline()
