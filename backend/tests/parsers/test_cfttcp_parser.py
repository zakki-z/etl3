"""Tests for migration_project.parsers.cfttcp_parser"""
from __future__ import annotations

import textwrap
from pathlib import Path

from migration_project.parsers.cfttcp_parser import parse_cfttcp


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "conf_cft.txt"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


class TestParseCfttcp:
    def test_single_entry_all_fields(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTTCP ID = 'PART01',
                CNXOUT = '5',
                HOST   = '192.168.1.10',
                MODE   = 'REPLACE'
        """)
        records = parse_cfttcp(p)
        assert len(records) == 1
        r = records[0]
        assert r.conf_id == "PART01"
        assert r.cnxout  == "5"
        assert r.host    == "192.168.1.10"

    def test_cnxout_missing_is_none(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTTCP ID = 'PART02',
                HOST = '10.0.0.1',
                MODE = 'REPLACE'
        """)
        records = parse_cfttcp(p)
        assert records[0].cnxout is None
        assert records[0].host   == "10.0.0.1"

    def test_entry_without_id_filtered(self, tmp_path: Path):
        # An entry where ID resolves to empty string should be dropped.
        p = _write(tmp_path, """\
            CFTTCP ID = '',
                HOST = '10.0.0.2',
                MODE = 'REPLACE'
        """)
        records = parse_cfttcp(p)
        assert records == []

    def test_multiple_entries(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTTCP ID = 'A',
                HOST = 'host-a',
                MODE = 'REPLACE'
            CFTTCP ID = 'B',
                HOST = 'host-b',
                CNXOUT = '3',
                MODE = 'REPLACE'
        """)
        records = parse_cfttcp(p)
        assert len(records) == 2
        by_id = {r.conf_id: r for r in records}
        assert by_id["A"].cnxout is None
        assert by_id["B"].cnxout == "3"

    def test_comment_lines_skipped(self, tmp_path: Path):
        p = _write(tmp_path, """\
            /* CFTTCP ID = 'SKIP', */
            CFTTCP ID = 'REAL',
                HOST = 'realhost',
                MODE = 'REPLACE'
        """)
        records = parse_cfttcp(p)
        assert len(records) == 1
        assert records[0].conf_id == "REAL"
