"""Tests for migration_project.parsers.boscosend_parser"""
from __future__ import annotations

import textwrap
from pathlib import Path

from migration_project.parsers.boscosend_parser import parse_boscosend_file


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "configuration.ini"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


class TestParseBoscosendFile:
    def test_valid_section_parsed(self, tmp_path: Path):
        p = _write(tmp_path, """\
            [SEND_IDF01_PARTNER_A]
            localDir     = D:\\CFT\\send\\PARTNER_A\\IDF01
            remoteAddress = 192.168.1.50
            remoteSubDir  = /incoming
            backupDir     = D:\\backup
            fileSearchMask = *.dat
            Cmdb-Prestation = PREST_01
        """)
        records = parse_boscosend_file(p)
        assert len(records) == 1
        r = records[0]
        assert r.nom_section    == "SEND_IDF01_PARTNER_A"
        assert r.remote_address == "192.168.1.50"
        assert r.remote_subdir  == "/incoming"
        assert r.backup_dir     is not None
        assert r.cmdb_prestation == "PREST_01"

    def test_cft_mapping_extracted_from_localdir(self, tmp_path: Path):
        p = _write(tmp_path, """\
            [SEC01]
            localDir      = C:\\data\\CFT\\send\\PARTNER_X\\MY_IDF
            remoteAddress = 10.0.0.1
        """)
        records = parse_boscosend_file(p)
        r = records[0]
        assert r.cft_direct    == "send"
        assert r.partner_code  == "PARTNER_X"
        assert r.idf_code      == "MY_IDF"

    def test_section_without_remote_address_skipped(self, tmp_path: Path):
        p = _write(tmp_path, """\
            [SCHEDULER_JOB]
            localDir = D:\\CFT\\send\\P1\\IDF1
        """)
        records = parse_boscosend_file(p)
        assert records == []

    def test_section_without_localdir_skipped(self, tmp_path: Path):
        p = _write(tmp_path, """\
            [UPLOAD_ONLY]
            remoteAddress = 10.0.0.2
        """)
        records = parse_boscosend_file(p)
        assert records == []

    def test_copilote_section_skipped(self, tmp_path: Path):
        p = _write(tmp_path, """\
            [copilote_sync]
            localDir      = D:\\copilote\\send\\P\\I
            remoteAddress = 10.0.0.3
        """)
        records = parse_boscosend_file(p)
        assert records == []

    def test_localdir_with_forward_slashes(self, tmp_path: Path):
        p = _write(tmp_path, """\
            [SEC_FWD]
            localDir      = /mnt/cft/send/PART_B/IDF_B
            remoteAddress = 10.0.0.4
        """)
        records = parse_boscosend_file(p)
        r = records[0]
        assert r.cft_direct   == "send"
        assert r.partner_code == "PART_B"
        assert r.idf_code     == "IDF_B"

    def test_multiple_valid_sections(self, tmp_path: Path):
        p = _write(tmp_path, """\
            [S1]
            localDir      = D:\\CFT\\send\\P1\\I1
            remoteAddress = 10.0.0.10

            [S2]
            localDir      = D:\\CFT\\recv\\P2\\I2
            remoteAddress = 10.0.0.11
        """)
        records = parse_boscosend_file(p)
        assert len(records) == 2

    def test_empty_file_returns_empty(self, tmp_path: Path):
        p = tmp_path / "configuration.ini"
        p.write_text("", encoding="utf-8")
        assert parse_boscosend_file(p) == []
