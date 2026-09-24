"""Load reference_data DDL from SQL files bundled under alembic/reference_data/."""
from __future__ import annotations

from pathlib import Path

from alembic import op

from migration_utils import execute_sql_files

REFERENCE_DATA_SQL_DIR = Path(__file__).resolve().parent / "reference_data"

# The 004 bootstrap snapshot, unchanged since it was published. Files added later are
# applied by their own revision (telus_functions.sql by 007), so each revision owns what
# it creates and a downgrade removes exactly what its upgrade installed.
REFERENCE_DATA_SCHEMA_FILES = (
    "schema.sql",
    "functions.sql",
    "sector.sql",
    "provider.sql",
    "bge.sql",
    "service_category.sql",
    "service_code.sql",
    "sub_bge.sql",
)


def execute_reference_data_sql_files() -> None:
    execute_sql_files(REFERENCE_DATA_SQL_DIR, REFERENCE_DATA_SCHEMA_FILES)


def execute_reference_data_files(*filenames: str) -> None:
    """Apply specific reference_data SQL files, so a later migration can pick up
    a changed definition without restating its body in the migration.

    Only for files that are safe to replay on a live database. functions.sql is
    NOT one of them: it ends with DROP FUNCTION IF EXISTS raw_data.norm_key(text),
    and IF EXISTS does not excuse a dependent object, so the drop is rejected once
    the Rogers cellular validation has built raw_data.v_rogers_cellular_validated
    on that function.
    """
    execute_sql_files(REFERENCE_DATA_SQL_DIR, filenames)


def drop_reference_data_schema() -> None:
    op.execute("DROP SCHEMA IF EXISTS reference_data CASCADE")
