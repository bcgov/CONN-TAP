"""Add raw_data tables for the new Telus NGTA pricebook v2 workbook format.

Revision ID: 007_telus_ngta_pricebook_v2
Revises: 006_telus_164_cellular_hardware
Create Date: 2026-09-02

TCI sent a new set of NGTA price books (Cellular Services v2.0, and four
more to follow) as single multi-sheet Excel workbooks, replacing the old
one-file-per-catalogue u_ngta_*.xlsx layout. This adds new raw_telus_v2_*
tables (DDL: alembic/raw_data/ngta_pricebooks_v2.sql) sized for that sheet
layout, in their own raw_data_v2 schema so they never collide with the
original raw_telus_* tables in raw_data (ngta_pricebooks.sql), which stay
untouched. pricebook_ingestion_run bookkeeping is shared and stays in
raw_data; the new tables reference it cross-schema.
"""
import importlib.util
from pathlib import Path
from typing import Sequence, Union

from alembic import op

_loader_path = Path(__file__).resolve().parent.parent.parent / "migration_utils.py"
_spec = importlib.util.spec_from_file_location("migration_utils_007", _loader_path)
_loader = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_loader)

_SQL_DIR = Path(__file__).resolve().parent.parent / "raw_data"

revision: str = "007_telus_ngta_pricebook_v2"
down_revision: Union[str, None] = "006_telus_164_cellular_hardware"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    _loader.execute_sql_files(_SQL_DIR, ("ngta_pricebooks_v2.sql",))


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS raw_data_v2 CASCADE")
