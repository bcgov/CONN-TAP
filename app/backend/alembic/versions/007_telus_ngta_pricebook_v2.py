"""Add raw_data tables for the new Telus NGTA pricebook v2 workbook format.

Revision ID: 007_telus_ngta_pricebook_v2
Revises: 006_telus_164_cellular_hardware
Create Date: 2026-09-02

TCI sent a new set of NGTA price books (Cellular Services v2.0, and four
more to follow) as single multi-sheet Excel workbooks, replacing the old
one-file-per-catalogue u_ngta_*.xlsx layout. This adds new raw_telus_v2_*
tables (DDL: alembic/raw_data/ngta_pricebooks_v2.sql) sized for that sheet
layout, in the raw_data schema next to pricebook_ingestion_run. The
*_v2_* names keep them distinct from the original raw_telus_*/raw_rogers_*
tables in ngta_pricebooks.sql, which stay untouched.
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


_V2_TABLES = (
    "raw_telus_v2_cellular_services_pricebook",
    "raw_telus_v2_cellular_additional_fee_based_features_pricebook",
    "raw_telus_v2_cellular_roaming_pricebook",
    "raw_telus_v2_cellular_long_distance_pricebook",
    "raw_telus_v2_cellular_mms_pricebook",
    "raw_telus_v2_gms_pricebook",
    "raw_telus_v2_gms_usage_rate_pricebook",
    "raw_telus_v2_control_center_pricebook",
    "raw_telus_v2_fleet_complete_pricebook",
    "raw_telus_v2_connected_worker_pricebook",
    "raw_telus_v2_connected_worker_usage_rate_pricebook",
    "raw_telus_v2_cellular_device_pricebook",
    "raw_telus_v2_connected_worker_hardware_pricebook",
    "raw_telus_v2_data_services_pricebook",
    "raw_telus_v2_voice_services_pricebook",
    "raw_telus_v2_voice_long_distance_fees_pricebook",
    "raw_telus_v2_voice_data_usage_rates_pricebook",
    "raw_telus_v2_tls_pricebook",
    "raw_telus_v2_professional_services_pricebook",
    "raw_telus_v2_connected_worker_professional_services_pricebook",
    "raw_rogers_v2_cellular_pricebook",
    "raw_rogers_v2_cellular_device_pricebook",
    "raw_rogers_v2_data_pricebook",
    "raw_rogers_v2_voice_pricebook",
    "raw_rogers_v2_professional_services_pricebook",
)


def downgrade() -> None:
    for table in _V2_TABLES:
        op.execute(f"DROP TABLE IF EXISTS raw_data.{table}")
