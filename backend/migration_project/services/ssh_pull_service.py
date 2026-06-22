from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import paramiko

from migration_project.config import get_settings
from migration_project.db import init_database, session_scope
from migration_project.models.server import Server
from migration_project.services.import_service import ImportService


# Allowed characters for server_id and remote paths (no shell metacharacters)
_SERVER_ID_RE = re.compile(r'^[A-Za-z0-9_\-]{1,50}$')
_SAFE_PATH_RE = re.compile(r'^[A-Za-z0-9_\-/\\.:@ ]{1,500}$')

# Filename pattern the pipeline expects
_CONF_PATTERN = "conf_cft.*.txt"


@dataclass
class SshPullReport:
    server_id: str
    host: str
    files_pulled: int = 0
    filenames: list[str] = field(default_factory=list)
    partner_parsed: int = 0
    partner_upserted: int = 0
    tcp_parsed: int = 0
    tcp_upserted: int = 0
    send_parsed: int = 0
    recv_parsed: int = 0
    flow_upserted: int = 0
    tcp_missing_partner: int = 0
    error: str | None = None


def _validate_server_id(server_id: str) -> None:
    if not _SERVER_ID_RE.match(server_id):
        raise ValueError(
            f"Invalid server_id '{server_id}'. "
            "Only alphanumeric characters, hyphens, and underscores are allowed."
        )


def _validate_path(path: str, label: str) -> None:
    if not _SAFE_PATH_RE.match(path):
        raise ValueError(f"Invalid {label}: contains unsafe characters.")


def _find_conf_files(sftp: paramiko.SFTPClient, remote_dir: str) -> list[str]:
    """List conf_cft.*.txt files in the remote directory."""
    import fnmatch
    try:
        entries = sftp.listdir(remote_dir)
    except FileNotFoundError:
        raise FileNotFoundError(f"Remote directory not found: {remote_dir}")

    return [
        entry for entry in entries
        if fnmatch.fnmatch(entry, _CONF_PATTERN)
    ]


def _download_files(
    sftp: paramiko.SFTPClient,
    remote_dir: str,
    filenames: list[str],
    local_dir: Path,
) -> list[Path]:
    """Download each file from remote_dir into local_dir."""
    local_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    for filename in filenames:
        remote_path = f"{remote_dir.rstrip('/')}/{filename}"
        local_path = local_dir / filename
        sftp.get(remote_path, str(local_path))
        downloaded.append(local_path)
    return downloaded


def _register_server(server_id: str, host: str, environment: str) -> None:
    """Upsert server row so the rest of the pipeline can reference it."""
    with session_scope() as session:
        existing = session.get(Server, server_id)
        if existing is None:
            session.add(Server(id=server_id, host=host, environment=environment))
        else:
            existing.host = host
            existing.environment = environment


def run_ssh_pull(
    *,
    server_id: str,
    host: str,
    port: int,
    username: str,
    password: str,
    remote_conf_dir: str,
    environment: str = "production",
) -> SshPullReport:
    """
    SSH into a CFT server, download conf_cft.*.txt files,
    save them under DATA_DIR/<server_id>/conf/, then run the import pipeline.

    Credentials are used once and never stored.
    """
    _validate_server_id(server_id)
    _validate_path(remote_conf_dir, "remote_conf_dir")

    report = SshPullReport(server_id=server_id, host=host)
    settings = get_settings()
    local_conf_dir = settings.data_dir / server_id / "conf"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=30,
            banner_timeout=30,
            auth_timeout=30,
            look_for_keys=False,
            allow_agent=False,
        )

        with ssh.open_sftp() as sftp:
            conf_filenames = _find_conf_files(sftp, remote_conf_dir)

            if not conf_filenames:
                report.error = (
                    f"No conf_cft.*.txt files found in {remote_conf_dir}. "
                    "Check the remote directory path."
                )
                return report

            local_paths = _download_files(sftp, remote_conf_dir, conf_filenames, local_conf_dir)

        report.files_pulled = len(local_paths)
        report.filenames = conf_filenames

    except paramiko.AuthenticationException:
        report.error = "SSH authentication failed. Check username and password."
        return report
    except paramiko.SSHException as e:
        report.error = f"SSH error: {e}"
        return report
    except FileNotFoundError as e:
        report.error = str(e)
        return report
    except OSError as e:
        report.error = f"Connection error: {e}"
        return report
    finally:
        ssh.close()

    # Register the server in the DB so the rest of the pipeline knows it
    init_database()
    _register_server(server_id, host, environment)

    # Run the import pipeline on the downloaded files
    import_report = ImportService().run_many(local_paths)

    report.partner_parsed = import_report.partner_parsed
    report.partner_upserted = import_report.partner_upserted
    report.tcp_parsed = import_report.tcp_parsed
    report.tcp_upserted = import_report.tcp_upserted
    report.send_parsed = import_report.send_parsed
    report.recv_parsed = import_report.recv_parsed
    report.flow_upserted = import_report.flow_upserted
    report.tcp_missing_partner = import_report.tcp_missing_partner

    return report