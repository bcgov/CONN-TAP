"""Create reference_data schema with sector and bge tables.

Revision ID: 003_reference_data_schema
Revises: 002_raw_data_schema
Create Date: 2026-06-09
"""
import importlib.util
from pathlib import Path
from typing import Sequence, Union

_loader_path = Path(__file__).resolve().parent.parent / "reference_data_loader.py"
_spec = importlib.util.spec_from_file_location("migration_reference_data_loader", _loader_path)
_loader = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_loader)

revision: str = "003_reference_data_schema"
down_revision: Union[str, None] = "002_raw_data_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    _loader.execute_reference_data_sql_files()


def downgrade() -> None:
    _loader.drop_reference_data_schema()
