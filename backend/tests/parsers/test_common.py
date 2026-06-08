"""Tests for migration_project.parsers.common"""
from __future__ import annotations

from pathlib import Path

import pytest

from migration_project.parsers.common import (
    extract_quoted,
    extract_value,
    iter_clean_lines,
    truncate,
)


class TestExtractQuoted:
    def test_simple_quoted_value(self):
        assert extract_quoted("NSPART = 'PARTNER_A'") == "PARTNER_A"

    def test_no_quotes_returns_none(self):
        assert extract_quoted("NSPART = PARTNER_A") is None

    def test_empty_quotes_returns_empty_string(self):
        assert extract_quoted("NSPART = ''") == ""

    def test_value_with_spaces_is_stripped(self):
        assert extract_quoted("NSPART = '  PARTNER_A  '") == "PARTNER_A"

    def test_first_quoted_value_wins(self):
        # Line with two quoted values — first one is returned.
        assert extract_quoted("A = 'first' /* 'second' */") == "first"

    def test_multichar_value(self):
        assert extract_quoted("CFTPART ID = 'MY_PARTNER_001'") == "MY_PARTNER_001"


class TestExtractValue:
    def test_quoted_value_preferred(self):
        assert extract_value("FNAME = '/data/out'") == "/data/out"

    def test_unquoted_value(self):
        assert extract_value("XLATE = YES") == "YES"

    def test_trailing_comma_stripped(self):
        assert extract_value("SAP = 1761,") == "1761"

    def test_trailing_semicolon_stripped(self):
        assert extract_value("SAP = 1761;") == "1761"

    def test_no_equals_returns_none(self):
        assert extract_value("JUSTWORDS") is None

    def test_empty_right_side_returns_none(self):
        assert extract_value("FNAME = ") is None

    def test_whitespace_right_side_returns_none(self):
        assert extract_value("FNAME =   ") is None


class TestTruncate:
    def test_short_value_unchanged(self):
        assert truncate("hello", 100) == "hello"

    def test_exact_max_len_unchanged(self):
        assert truncate("ab", 2) == "ab"

    def test_long_value_truncated(self):
        assert truncate("abcdefg", 3) == "abc"

    def test_none_returns_none(self):
        assert truncate(None, 100) is None

    def test_empty_string_returns_none(self):
        assert truncate("", 100) is None

    def test_whitespace_only_returns_none(self):
        assert truncate("   ", 100) is None

    def test_strips_before_check(self):
        # Leading/trailing spaces are stripped; result may become short enough.
        assert truncate("  ab  ", 3) == "ab"


class TestIterCleanLines:
    def test_skips_blank_lines(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("\nHELLO\n\nWORLD\n", encoding="utf-8")
        assert list(iter_clean_lines(f)) == ["HELLO", "WORLD"]

    def test_skips_comment_lines(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("/* this is a comment */\nVALID_LINE\n", encoding="utf-8")
        assert list(iter_clean_lines(f)) == ["VALID_LINE"]

    def test_strips_whitespace(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("  TRIMMED_LINE  \n", encoding="utf-8")
        assert list(iter_clean_lines(f)) == ["TRIMMED_LINE"]
