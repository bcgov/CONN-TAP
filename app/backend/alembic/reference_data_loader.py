"""Load reference_data DDL from SQL files bundled under alembic/reference_data/."""
from __future__ import annotations

from pathlib import Path

from alembic import op

from migration_utils import execute_sql_files

REFERENCE_DATA_SQL_DIR = Path(__file__).resolve().parent / "reference_data"

REFERENCE_DATA_SCHEMA_FILES = (
    "schema.sql",
    "sector.sql",
    "provider.sql",
    "bge.sql",
    "service_category.sql",
    "service_code.sql",
    "sub_bge.sql",
)


def execute_reference_data_sql_files() -> None:
    execute_sql_files(REFERENCE_DATA_SQL_DIR, REFERENCE_DATA_SCHEMA_FILES)


def drop_reference_data_schema() -> None:
    op.execute("DROP SCHEMA IF EXISTS reference_data CASCADE")
