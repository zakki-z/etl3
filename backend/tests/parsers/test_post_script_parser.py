"""Tests for migration_project.parsers.post_script_parser"""
from __future__ import annotations

import textwrap
from pathlib import Path

from migration_project.parsers.post_script_parser import (
    parse_global_script,
    parse_specific_script,
    script_direction,
)


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    # Strip common leading whitespace so bat lines start at column 0,
    # which is required for the regex anchors in the parser.
    p.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
    return p


class TestScriptDirection:
    def test_recvok(self):  assert script_direction("RECVOK.bat")  == "recv"
    def test_recvnok(self): assert script_direction("RECVNOK.bat") == "recv"
    def test_sendok(self):  assert script_direction("SENDOK.bat")  == "send"
    def test_sendnok(self): assert script_direction("SENDNOK.bat") == "send"
    def test_unknown(self): assert script_direction("OTHER.bat")   is None
    def test_case_insensitive(self): assert script_direction("recvok.bat") == "recv"


class TestParseGlobalScript:
    def test_if_idf_goto_block_captured(self, tmp_path: Path):
        p = _write(tmp_path, "RECVOK.bat", """\
@echo off
if &IDF==MY_IDF goto DO_SOMETHING

:DO_SOMETHING
xcopy /Y src dest
""")
        actions = parse_global_script(p, direct="recv")
        assert len(actions) >= 1
        idf_actions = [a for a in actions if a.scope_type == "IDF" and a.idf_code == "MY_IDF"]
        assert len(idf_actions) >= 1
        assert any("xcopy" in a.action_text for a in idf_actions)

    def test_if_part_goto_block_captured(self, tmp_path: Path):
        p = _write(tmp_path, "RECVOK.bat", """\
@echo off
if &PART==PARTNER_A goto NOTIFY

:NOTIFY
net_send_ok.exe PARTNER_A
""")
        actions = parse_global_script(p, direct="recv")
        part_actions = [a for a in actions if a.scope_type == "PART"]
        assert len(part_actions) >= 1
        assert part_actions[0].partner_id == "PARTNER_A"

    def test_comments_and_technical_lines_skipped(self, tmp_path: Path):
        p = _write(tmp_path, "SENDOK.bat", """\
@echo off
REM This is a comment
setlocal
:: another comment
if &IDF==IDF1 goto DO

:DO
echo doing something
""")
        actions = parse_global_script(p, direct="send")
        assert all("echo off" not in a.action_text for a in actions)
        assert all("setlocal" not in a.action_text for a in actions)

    def test_gmcft_lines_skipped(self, tmp_path: Path):
        p = _write(tmp_path, "RECVOK.bat", """\
@echo off
if &IDF==IDF_X goto DO

:DO
gmCft.exe some_command
legitimate_command.exe
""")
        actions = parse_global_script(p, direct="recv")
        assert all("gmcft" not in a.action_text.lower() for a in actions)

    def test_empty_script_returns_empty(self, tmp_path: Path):
        p = _write(tmp_path, "RECVOK.bat", "@echo off\n")
        assert parse_global_script(p, direct="recv") == []

    def test_action_order_increments_per_idf(self, tmp_path: Path):
        p = _write(tmp_path, "RECVOK.bat", """\
@echo off
if &IDF==IDF_A goto BLOCK_A

:BLOCK_A
cmd_1.exe
cmd_2.exe
""")
        actions = parse_global_script(p, direct="recv")
        idf_actions = [a for a in actions if a.idf_code == "IDF_A"]
        assert len(idf_actions) >= 1
        orders = [a.action_order for a in idf_actions]
        assert orders == sorted(orders)
        assert orders[0] == 1


class TestParseSpecificScript:
    def test_all_non_technical_lines_captured(self, tmp_path: Path):
        p = _write(tmp_path, "IDF_SPECIAL.bat", """\
@echo off
setlocal
xcopy /Y D:\\in\\%1 D:\\archive\\
echo done
endlocal
""")
        actions = parse_specific_script(p, direct="send", idf_code="IDF_SPECIAL")
        texts = [a.action_text for a in actions]
        assert any("xcopy" in t for t in texts)
        assert all("setlocal" not in t for t in texts)

    def test_scope_is_idf_script(self, tmp_path: Path):
        p = _write(tmp_path, "MY_IDF.bat", """\
@echo off
do_something.exe
""")
        actions = parse_specific_script(p, direct="recv", idf_code="MY_IDF")
        assert all(a.scope_type == "IDF_SCRIPT" for a in actions)
        assert all(a.idf_code == "MY_IDF" for a in actions)

    def test_conditional_if_part_kept_verbatim(self, tmp_path: Path):
        p = _write(tmp_path, "IDF_COND.bat", """\
@echo off
if &PART==PARTNER_X copy_to_partner.exe
""")
        actions = parse_specific_script(p, direct="send", idf_code="IDF_COND")
        assert any("&PART" in a.action_text for a in actions)