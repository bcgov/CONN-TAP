"""Create raw_data landing schema and tables for NGTA/TSMA ingestion.

Revision ID: 002_raw_data_schema
Revises: 001_initial_app_schema
Create Date: 2026-05-25

DDL source files live in alembic/raw_data/ (moved from local_dev/raw_ingestion).
"""
import importlib.util
from pathlib import Path
from typing import Sequence, Union

_loader_path = Path(__file__).resolve().parent.parent / "raw_data_loader.py"
_spec = importlib.util.spec_from_file_location("migration_raw_data_loader", _loader_path)
_loader = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_loader)

revision: str = "002_raw_data_schema"
down_revision: Union[str, None] = "001_initial_app_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    _loader.execute_raw_data_sql_files()


def downgrade() -> None:
    _loader.drop_raw_data_schema()
