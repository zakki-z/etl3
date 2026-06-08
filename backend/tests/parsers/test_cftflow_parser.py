"""Tests for migration_project.parsers.cftflow_parser"""
from __future__ import annotations

import textwrap
from pathlib import Path

from migration_project.parsers.cftflow_parser import parse_cftrecv, parse_cftsend


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "conf_cft.txt"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


class TestParseCftsend:
    def test_basic_send_flow(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTSEND ID = 'IDF_SEND01',
                FCODE  = 'BINARY',
                FTYPE  = 'B',
                FLRECL = '0',
                FNAME  = '/data/out/file.dat',
                XLATE  = '',
                MODE   = 'REPLACE'
        """)
        records = parse_cftsend(p)
        assert len(records) == 1
        r = records[0]
        assert r.idf_code == "IDF_SEND01"
        assert r.direct   == "send"
        assert r.fcode    == "BINARY"
        assert r.ftype    == "B"
        assert r.flrecl   == "0"
        assert r.fname    == "/data/out/file.dat"
        assert r.xlate    == 0

    def test_xlate_non_empty_is_one(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTSEND ID = 'IDF01',
                XLATE  = 'ISO8859',
                MODE   = 'REPLACE'
        """)
        records = parse_cftsend(p)
        assert records[0].xlate == 1

    def test_exec_and_exece_captured(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTSEND ID = 'IDF_EXEC',
                EXEC   = 'D:\\\\Scripts\\\\SENDOK.bat',
                EXECE  = 'D:\\\\Scripts\\\\SENDNOK.bat',
                MODE   = 'REPLACE'
        """)
        records = parse_cftsend(p)
        assert records[0].exec  is not None
        assert records[0].exece is not None
        assert "SENDOK" in records[0].exec
        assert "SENDNOK" in records[0].exece

    def test_commented_frecfm_is_null(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTSEND ID = 'IDF_FREQ',
                /* FRECFM = 'F', */
                FLRECL = '80',
                MODE = 'REPLACE'
        """)
        records = parse_cftsend(p)
        assert records[0].frecfm is None

    def test_multiple_flows(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTSEND ID = 'FLOW_A',
                FCODE = 'ASCII',
                MODE  = 'REPLACE'
            CFTSEND ID = 'FLOW_B',
                FCODE = 'BINARY',
                MODE  = 'REPLACE'
        """)
        records = parse_cftsend(p)
        assert len(records) == 2
        assert {r.idf_code for r in records} == {"FLOW_A", "FLOW_B"}

    def test_no_send_blocks_returns_empty(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTPART ID = 'P1',
                NSPART = 'NS1',
                NRPART = 'NR1',
                MODE = 'REPLACE'
        """)
        assert parse_cftsend(p) == []

    def test_fname_truncated_to_100_chars(self, tmp_path: Path):
        long_path = "/data/" + "a" * 200
        p = _write(tmp_path, f"""\
            CFTSEND ID = 'LONG',
                FNAME = '{long_path}',
                MODE  = 'REPLACE'
        """)
        records = parse_cftsend(p)
        assert records[0].fname is not None
        assert len(records[0].fname) <= 100


class TestParseCftrecv:
    def test_basic_recv_flow(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTRECV ID = 'IDF_RECV01',
                FCODE  = 'BINARY',
                FNAME  = '/data/in/',
                MODE   = 'REPLACE'
        """)
        records = parse_cftrecv(p)
        assert len(records) == 1
        assert records[0].idf_code == "IDF_RECV01"
        assert records[0].direct   == "recv"

    def test_send_blocks_not_included_in_recv(self, tmp_path: Path):
        p = _write(tmp_path, """\
            CFTSEND ID = 'SEND01',
                MODE = 'REPLACE'
            CFTRECV ID = 'RECV01',
                MODE = 'REPLACE'
        """)
        recv_records = parse_cftrecv(p)
        assert all(r.direct == "recv" for r in recv_records)
        assert len(recv_records) == 1

    def test_exece_field_precedence_over_exec(self, tmp_path: Path):
        """EXECE must not be confused with EXEC when field parsing."""
        p = _write(tmp_path, """\
            CFTRECV ID = 'IDF_BOTH',
                EXEC  = 'D:\\\\Scripts\\\\RECVOK.bat',
                EXECE = 'D:\\\\Scripts\\\\RECVNOK.bat',
                MODE  = 'REPLACE'
        """)
        records = parse_cftrecv(p)
        r = records[0]
        assert r.exec  is not None
        assert r.exece is not None
        assert "RECVOK"  in r.exec
        assert "RECVNOK" in r.exece
