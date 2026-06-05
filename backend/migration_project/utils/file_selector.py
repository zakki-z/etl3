from __future__ import annotations

from pathlib import Path


def get_latest_file(directory: Path, pattern: str) -> Path:
    files = list(directory.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No file found in '{directory}' with pattern '{pattern}'")
    return max(files, key=lambda item: item.stat().st_mtime)


def get_matching_files(directory: Path, pattern: str) -> list[Path]:
    files = [file for file in directory.glob(pattern) if file.is_file()]
    if not files:
        raise FileNotFoundError(f"No file found in '{directory}' with pattern '{pattern}'")
    # Stable order for deterministic runs across environments.
    return sorted(files, key=lambda item: (item.stat().st_mtime, item.name))


def get_matching_server_conf_files(data_dir: Path, pattern: str) -> list[Path]:
    files: list[Path] = []
    for server_dir in sorted(path for path in data_dir.iterdir() if path.is_dir()):
        conf_dir = server_dir / "conf"
        if not conf_dir.is_dir():
            continue
        files.extend(file for file in conf_dir.glob(pattern) if file.is_file())

    if not files:
        raise FileNotFoundError(
            f"No configuration file found under '{data_dir}/<server>/conf' with pattern '{pattern}'"
        )
    # Stable order: server folder first, then file mtime/name inside each server.
    return sorted(files, key=lambda item: (item.parent.parent.name, item.stat().st_mtime, item.name))


def get_server_script_dirs(data_dir: Path) -> list[tuple[str, Path]]:
    """Return [(server_id, scripts_dir), ...] for every <data_dir>/<server>/scripts."""
    pairs: list[tuple[str, Path]] = []
    if not data_dir.is_dir():
        return pairs
    for server_dir in sorted(path for path in data_dir.iterdir() if path.is_dir()):
        scripts_dir = server_dir / "scripts"
        if scripts_dir.is_dir():
            pairs.append((server_dir.name, scripts_dir))
    return pairs


def get_server_moncft_dirs(data_dir: Path) -> list[tuple[str, Path]]:
    """Return [(server_id, moncft_dir), ...] for every <data_dir>/<server>/moncft."""
    pairs: list[tuple[str, Path]] = []
    if not data_dir.is_dir():
        return pairs
    for server_dir in sorted(path for path in data_dir.iterdir() if path.is_dir()):
        moncft_dir = server_dir / "moncft"
        if moncft_dir.is_dir():
            pairs.append((server_dir.name, moncft_dir))
    return pairs


def get_server_boscosend_files(data_dir: Path) -> list[tuple[str, Path]]:
    """Return [(server_id, configuration.ini), ...] for every boscosend config."""
    pairs: list[tuple[str, Path]] = []
    if not data_dir.is_dir():
        return pairs
    for server_dir in sorted(path for path in data_dir.iterdir() if path.is_dir()):
        config_file = server_dir / "boscosend" / "configuration.ini"
        if config_file.is_file():
            pairs.append((server_dir.name, config_file))
    return pairs
