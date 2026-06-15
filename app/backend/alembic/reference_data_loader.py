"""Load reference_data DDL from SQL files bundled under alembic/reference_data/."""
from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa
from alembic import op

REFERENCE_DATA_SQL_DIR = Path(__file__).resolve().parent / "reference_data"

REFERENCE_DATA_SCHEMA_FILES = (
    "schema.sql",
    "sector.sql",
    "provider.sql",
    "service_category.sql",
    "service_code.sql",
    "bge.sql",
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


def execute_reference_data_sql_files() -> None:
    connection = op.get_bind()
    for filename in REFERENCE_DATA_SCHEMA_FILES:
        path = REFERENCE_DATA_SQL_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing reference_data DDL file: {path}")
        for statement in _split_sql_statements(path.read_text(encoding="utf-8")):
            connection.execute(sa.text(statement))


def drop_reference_data_schema() -> None:
    op.execute("DROP SCHEMA IF EXISTS reference_data CASCADE")
