import getpass
import logging
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("cft_extractor")
def pull_data_via_ssh(
    remote_host: str,
    remote_user: str,
    remote_data_dir: str,
    local_dest: str,
    remote_port: int = 22,
    ssh_key_path: Optional[str] = None,
    ssh_password: Optional[str] = None,
) -> Path:
    """
    Pull CFT data from the remote Ubuntu VM to a local directory via SSH/SCP.

    Supports three auth methods (tried in order):
      1. SSH key file (if ssh_key_path is provided)
      2. SSH agent (keys already loaded via ssh-add)
      3. Password (interactive prompt if ssh_password is None)

    Returns the local Path where data was downloaded.
    """
    local_path = Path(local_dest)
    local_path.mkdir(parents=True, exist_ok=True)

    log.info(f"Pulling data from {remote_user}@{remote_host}:{remote_data_dir}")
    log.info(f"  → local destination: {local_path}")

    # ── Try paramiko first (pure Python, no external deps) ───────────────
    try:
        import paramiko

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": remote_host,
            "port": remote_port,
            "username": remote_user,
        }

        if ssh_key_path:
            log.info(f"  Auth: SSH key → {ssh_key_path}")
            connect_kwargs["key_filename"] = os.path.expanduser(ssh_key_path)
        elif ssh_password:
            log.info("  Auth: password")
            connect_kwargs["password"] = ssh_password
        else:
            # Try agent first, fall back to password prompt
            log.info("  Auth: SSH agent / interactive")
            connect_kwargs["allow_agent"] = True
            connect_kwargs["look_for_keys"] = True

        try:
            ssh.connect(**connect_kwargs)
        except (paramiko.ssh_exception.AuthenticationException,
                paramiko.ssh_exception.SSHException) as e:
            if not ssh_password and not ssh_key_path:
                log.info("  SSH agent failed, prompting for password...")
                ssh_password = getpass.getpass(
                    f"  Password for {remote_user}@{remote_host}: "
                )
                ssh.connect(
                    hostname=remote_host,
                    port=remote_port,
                    username=remote_user,
                    password=ssh_password,
                )
            else:
                raise

        sftp = ssh.open_sftp()
        _sftp_pull_recursive(sftp, remote_data_dir, str(local_path))
        sftp.close()
        ssh.close()

        log.info("  SSH/SFTP download complete.")
        return local_path

    except ImportError:
        log.info("  paramiko not installed, falling back to scp/rsync...")

    #Fallback: rsync or scp via subprocess
    ssh_opts = ["-o", "StrictHostKeyChecking=no", "-p", str(remote_port)]
    if ssh_key_path:
        ssh_opts += ["-i", os.path.expanduser(ssh_key_path)]

    # Try rsync first (better for incremental refresh)
    if shutil.which("rsync"):
        cmd = [
            "rsync", "-avz", "--progress",
            "-e", f"ssh {' '.join(ssh_opts)}",
            f"{remote_user}@{remote_host}:{remote_data_dir}/",
            f"{local_path}/",
        ]
        log.info(f"  Running: rsync from {remote_host}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            log.info("  rsync download complete.")
            return local_path
        else:
            log.warning(f"  rsync failed: {result.stderr.strip()}")
            log.info("  Falling back to scp...")

    # scp fallback
    cmd = [
        "scp", "-r",
        *ssh_opts,
        f"{remote_user}@{remote_host}:{remote_data_dir}",
        str(local_path.parent),
    ]
    log.info(f"  Running: scp from {remote_host}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(f"  scp failed: {result.stderr.strip()}")
        sys.exit(1)

    # scp copies into parent as the dir name
    scp_result = local_path.parent / Path(remote_data_dir).name
    if scp_result != local_path and scp_result.exists():
        # Move contents into local_path
        for item in scp_result.iterdir():
            dest = local_path / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(item), str(dest))
        scp_result.rmdir()

    log.info("  scp download complete.")
    return local_path


def _sftp_pull_recursive(sftp, remote_path: str, local_path: str):
    """Recursively download a remote directory via SFTP."""

    os.makedirs(local_path, exist_ok=True)

    for entry in sftp.listdir_attr(remote_path):
        remote_entry = f"{remote_path}/{entry.filename}"
        local_entry = os.path.join(local_path, entry.filename)

        if stat.S_ISDIR(entry.st_mode):
            _sftp_pull_recursive(sftp, remote_entry, local_entry)
        else:
            log.debug(f"    Downloading: {remote_entry}")
            sftp.get(remote_entry, local_entry)