"""Load raw_data DDL from SQL files bundled under alembic/raw_data/."""
from __future__ import annotations

from pathlib import Path

from alembic import op

from migration_utils import execute_sql_files

RAW_DATA_SQL_DIR = Path(__file__).resolve().parent / "raw_data"

# Order matters when cross-table references exist within the same schema.
RAW_DATA_SCHEMA_FILES = (
    "ngta_postgres.sql",
    "ngta_pricebooks.sql",
    "tsma_postgres.sql",
    "tsma_other_postgres.sql",
)


def execute_raw_data_sql_files() -> None:
    execute_sql_files(RAW_DATA_SQL_DIR, RAW_DATA_SCHEMA_FILES)


def drop_raw_data_schema() -> None:
    op.execute("DROP SCHEMA IF EXISTS raw_data CASCADE")
