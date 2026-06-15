"""Create reference_data schema with all lookup tables and seed data.

Revision ID: 004_reference_data_schema
Revises: 003_datasets_registry
Create Date: 2026-06-11

"""
import importlib.util
from pathlib import Path
from typing import Sequence, Union

_loader_path = Path(__file__).resolve().parent.parent / "reference_data_loader.py"
_spec = importlib.util.spec_from_file_location("migration_reference_data_loader", _loader_path)
_loader = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_loader)

revision: str = "004_reference_data_schema"
down_revision: Union[str, Sequence[str], None] = "003_datasets_registry"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    _loader.execute_reference_data_sql_files()


def downgrade() -> None:
    _loader.drop_reference_data_schema()
