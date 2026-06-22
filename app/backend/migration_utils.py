"""SQL file execution helpers shared by alembic schema loaders."""
from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa
from alembic import op


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


def execute_sql_files(sql_dir: Path, files: tuple[str, ...]) -> None:
    connection = op.get_bind()
    for filename in files:
        path = sql_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing DDL file: {path}")
        for statement in _split_sql_statements(path.read_text(encoding="utf-8")):
            connection.execute(sa.text(statement))
