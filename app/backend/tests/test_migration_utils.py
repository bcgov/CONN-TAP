from pathlib import Path
from unittest.mock import patch

import pytest

from migration_utils import _strip_sql_comments, _split_sql_statements, execute_sql_files


def test_strip_sql_comments_removes_comment_lines() -> None:
    sql = "SELECT 1;\n-- a comment\nSELECT 2;"
    assert "-- a comment" not in _strip_sql_comments(sql)


def test_strip_sql_comments_keeps_non_comment_lines() -> None:
    sql = "SELECT 1;\n-- comment\nSELECT 2;"
    result = _strip_sql_comments(sql)
    assert "SELECT 1;" in result
    assert "SELECT 2;" in result


def test_split_sql_statements_splits_on_semicolon() -> None:
    sql = "SELECT 1; SELECT 2; SELECT 3"
    statements = _split_sql_statements(sql)
    assert len(statements) == 3


def test_split_sql_statements_ignores_comment_lines() -> None:
    sql = "SELECT 1;\n-- comment\nSELECT 2;"
    statements = _split_sql_statements(sql)
    assert len(statements) == 2


def test_split_sql_statements_empty_input() -> None:
    assert _split_sql_statements("") == []


def test_execute_sql_files_raises_for_missing_file(tmp_path: Path) -> None:
    with patch("migration_utils.op"), pytest.raises(FileNotFoundError):
        execute_sql_files(tmp_path, ("missing.sql",))
