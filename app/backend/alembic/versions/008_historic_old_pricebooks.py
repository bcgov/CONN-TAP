"""Move the original (pre-v2) NGTA price book tables into historic_data.

Revision ID: 008_historic_old_pricebooks
Revises: 007_telus_ngta_pricebook_v2
Create Date: 2026-09-21

The v2 price books (raw_telus_v2_* / raw_rogers_v2_*, migration 007) are now
the reference tables and stay in raw_data. The original one-file-per-catalogue
tables are kept as historic data in the historic_data schema.
raw_data.pricebook_ingestion_run stays in raw_data (the v2 tables reference
it; foreign keys from the moved tables keep working across schemas).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "008_historic_old_pricebooks"
down_revision: Union[str, None] = "007_telus_ngta_pricebook_v2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_TABLES = (
    "raw_rogers_professional_services_pricebook",
    "raw_rogers_data_pricebook",
    "raw_rogers_cellular_pricebook",
    "raw_rogers_voice_pricebook",
    "raw_telus_cellular_additional_fees_pricebook",
    "raw_telus_cellular_catalog_and_price_list_pricebook",
    "raw_telus_cellular_device_pricebook",
    "raw_telus_cellular_long_distance_cost_per_minute_pricebook",
    "raw_telus_cellular_mms_pricebook",
    "raw_telus_cellular_roaming_pricebook",
    "raw_telus_cellular_services_pricebook",
    "raw_telus_control_center_services_pricebook",
    "raw_telus_data_professional_services_pricebook",
    "raw_telus_data_services_pricebook",
    "raw_telus_voice_long_distance_fees_pricebook",
    "raw_telus_voice_professional_services_pricebook",
    "raw_telus_voice_services_pricebook",
)


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS historic_data")
    for table in _OLD_TABLES:
        op.execute(f"ALTER TABLE IF EXISTS raw_data.{table} SET SCHEMA historic_data")


def downgrade() -> None:
    for table in _OLD_TABLES:
        op.execute(f"ALTER TABLE IF EXISTS historic_data.{table} SET SCHEMA raw_data")
    op.execute("DROP SCHEMA IF EXISTS historic_data")
