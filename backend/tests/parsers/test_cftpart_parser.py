"""Tests for migration_project.parsers.cftpart_parser"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from migration_project.parsers.cftpart_parser import parse_cftpart
from migration_project.parsers.records import PartnerRecord


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "conf_cft.txt"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


class TestParseCftpart:
    def test_single_partner_all_fields(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTPART ID = 'PART01',
                NSPART = 'NS_PART01',
                NRPART = 'NR_PART01',
                IPART  = 'IP_PART01',
                SAP    = '1761',
                NSPASSW = 'pass_ns',
                NRPASSW = 'pass_nr',
                SSL    = 'YES',
                MODE   = 'REPLACE'
        """)
        records = parse_cftpart(p)
        assert len(records) == 1
        r = records[0]
        assert r.conf_id   == "PART01"
        assert r.nspart    == "NS_PART01"
        assert r.nrpart    == "NR_PART01"
        assert r.ipart     == "IP_PART01"
        assert r.sap       == "1761"
        assert r.nspassw   == "pass_ns"
        assert r.nrpassw   == "pass_nr"
        assert r.ssl       == 1

    def test_partner_without_ssl_defaults_to_zero(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTPART ID = 'PART02',
                NSPART = 'NS2',
                NRPART = 'NR2',
                MODE   = 'REPLACE'
        """)
        records = parse_cftpart(p)
        assert records[0].ssl == 0

    def test_partner_without_nspart_or_nrpart_is_filtered(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTPART ID = 'PART03',
                MODE   = 'REPLACE'
        """)
        records = parse_cftpart(p)
        assert records == []

    def test_multiple_partners(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTPART ID = 'A',
                NSPART = 'NS_A',
                NRPART = 'NR_A',
                MODE = 'REPLACE'
            CFTPART ID = 'B',
                NSPART = 'NS_B',
                NRPART = 'NR_B',
                MODE = 'REPLACE'
        """)
        records = parse_cftpart(p)
        assert len(records) == 2
        assert {r.conf_id for r in records} == {"A", "B"}

    def test_comment_lines_ignored(self, tmp_path: Path):
        p = _write(tmp_path, """\
            /* This is a comment block */
            CFTPART ID = 'PART04',
                NSPART = 'NS4',
                NRPART = 'NR4',
                /* SSL = 'YES', */
                MODE = 'REPLACE'
        """)
        records = parse_cftpart(p)
        assert len(records) == 1
        assert records[0].ssl == 0

    def test_empty_file_returns_empty(self, tmp_path: Path):
        p = tmp_path / "empty.txt"
        p.write_text("", encoding="utf-8")
        assert parse_cftpart(p) == []

    def test_ssl_empty_value_is_zero(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTPART ID = 'PART05',
                NSPART = 'NS5',
                NRPART = 'NR5',
                SSL = '',
                MODE = 'REPLACE'
        """)
        records = parse_cftpart(p)
        assert records[0].ssl == 0

    def test_ipart_optional_field(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTPART ID = 'PART06',
                NSPART = 'NS6',
                NRPART = 'NR6',
                IPART  = 'IP6',
                MODE   = 'REPLACE'
        """)
        records = parse_cftpart(p)
        assert records[0].ipart == "IP6"
