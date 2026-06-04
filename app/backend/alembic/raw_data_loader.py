"""Load raw_data DDL from SQL files bundled under alembic/raw_data/."""
from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa
from alembic import op

RAW_DATA_SQL_DIR = Path(__file__).resolve().parent / "raw_data"

# Order matters when cross-table references exist within the same schema.
RAW_DATA_SCHEMA_FILES = (
    "ngta_postgres.sql",
    "ngta_pricebooks.sql",
    "tsma_postgres.sql",
    "tsma_other_postgres.sql",
)


def _strip_sql_comments(sql: str) -> str:
    lines: list[str] = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(line)
    return "\n".join(lines)


def _split_sql_statements(sql: str) -> list[str]:
    body = _strip_sql_comments(sql)
    return [part.strip() for part in body.split(";") if part.strip()]


def execute_raw_data_sql_files() -> None:
    connection = op.get_bind()
    for filename in RAW_DATA_SCHEMA_FILES:
        path = RAW_DATA_SQL_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing raw_data DDL file: {path}")
        for statement in _split_sql_statements(path.read_text(encoding="utf-8")):
            connection.execute(sa.text(statement))


def drop_raw_data_schema() -> None:
    op.execute("DROP SCHEMA IF EXISTS raw_data CASCADE")
