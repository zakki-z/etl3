"""Tests for migration_project.utils.file_selector"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from migration_project.utils.file_selector import (
    get_latest_file,
    get_matching_files,
    get_matching_server_conf_files,
    get_server_boscosend_files,
    get_server_moncft_dirs,
    get_server_script_dirs,
)


class TestGetLatestFile:
    def test_returns_most_recent_file(self, tmp_path: Path):
        old = tmp_path / "conf_cft.20260101.txt"
        old.write_text("old")
        time.sleep(0.01)
        new = tmp_path / "conf_cft.20260422.txt"
        new.write_text("new")
        result = get_latest_file(tmp_path, "conf_cft.*.txt")
        assert result == new

    def test_raises_when_no_match(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            get_latest_file(tmp_path, "conf_cft.*.txt")


class TestGetMatchingFiles:
    def test_returns_sorted_by_mtime(self, tmp_path: Path):
        a = tmp_path / "conf_cft.20260101.txt"
        a.write_text("a")
        time.sleep(0.01)
        b = tmp_path / "conf_cft.20260201.txt"
        b.write_text("b")
        files = get_matching_files(tmp_path, "conf_cft.*.txt")
        assert files[0] == a
        assert files[1] == b

    def test_ignores_directories(self, tmp_path: Path):
        (tmp_path / "conf_cft.dir.txt").mkdir()
        (tmp_path / "conf_cft.file.txt").write_text("x")
        files = get_matching_files(tmp_path, "conf_cft.*.txt")
        assert all(f.is_file() for f in files)

    def test_raises_when_empty(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            get_matching_files(tmp_path, "*.txt")


class TestGetMatchingServerConfFiles:
    def _make_server_conf(self, base: Path, server: str, filename: str) -> Path:
        conf_dir = base / server / "conf"
        conf_dir.mkdir(parents=True, exist_ok=True)
        p = conf_dir / filename
        p.write_text("data")
        return p

    def test_finds_conf_files_in_server_subdirs(self, tmp_path: Path):
        self._make_server_conf(tmp_path, "SRV01", "conf_cft.20260422.txt")
        self._make_server_conf(tmp_path, "SRV02", "conf_cft.20260422.txt")
        files = get_matching_server_conf_files(tmp_path, "conf_cft.*.txt")
        assert len(files) == 2

    def test_raises_when_no_conf_found(self, tmp_path: Path):
        (tmp_path / "SRV01").mkdir()  # no conf/ subdir
        with pytest.raises(FileNotFoundError):
            get_matching_server_conf_files(tmp_path, "conf_cft.*.txt")


class TestGetServerScriptDirs:
    def test_returns_pairs_for_scripts_dirs(self, tmp_path: Path):
        for srv in ["SRV01", "SRV02"]:
            (tmp_path / srv / "scripts").mkdir(parents=True)

        pairs = get_server_script_dirs(tmp_path)
        assert len(pairs) == 2
        assert all(p[1].name == "scripts" for p in pairs)

    def test_ignores_servers_without_scripts_dir(self, tmp_path: Path):
        (tmp_path / "SRV01").mkdir()  # no scripts/
        (tmp_path / "SRV02" / "scripts").mkdir(parents=True)
        pairs = get_server_script_dirs(tmp_path)
        assert len(pairs) == 1

    def test_nonexistent_data_dir_returns_empty(self, tmp_path: Path):
        assert get_server_script_dirs(tmp_path / "nonexistent") == []


class TestGetServerMoncftDirs:
    def test_returns_pairs_for_moncft_dirs(self, tmp_path: Path):
        (tmp_path / "SRV01" / "moncft").mkdir(parents=True)
        pairs = get_server_moncft_dirs(tmp_path)
        assert len(pairs) == 1
        assert pairs[0][0] == "SRV01"


class TestGetServerBoscosendFiles:
    def test_returns_pairs_for_config_ini(self, tmp_path: Path):
        boscosend_dir = tmp_path / "SRV01" / "boscosend"
        boscosend_dir.mkdir(parents=True)
        (boscosend_dir / "configuration.ini").write_text("[S1]\nfoo=bar")
        pairs = get_server_boscosend_files(tmp_path)
        assert len(pairs) == 1
        assert pairs[0][1].name == "configuration.ini"

    def test_ignores_servers_without_boscosend(self, tmp_path: Path):
        (tmp_path / "SRV01").mkdir()
        assert get_server_boscosend_files(tmp_path) == []
