"""Add the Telus hardware-matching functions.

Revision ID: 007_telus_detail_signature
Revises: 006_telus_164_cellular_hardware
Create Date: 2026-09-23

telus_detail_signature reduces a detail_description to its word signature, and
telus_is_hardware_detail tests that signature against the dbt seed
telus_hardware_details. See scripts/sql/telus_classification.md for why the match is
on signatures rather than literal text, and for the confirmed hardware families.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "007_telus_detail_signature"
down_revision: Union[str, None] = "006_telus_164_cellular_hardware"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SIGNATURE = r"""
CREATE OR REPLACE FUNCTION reference_data.telus_detail_signature(col text)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT btrim(regexp_replace(
        regexp_replace(
            regexp_replace(lower(coalesce(col, '')), '\(.*?\)', ' ', 'g'),
            '\(.*$', ' '),
        '[^a-z]+', ' ', 'g'))
$$
"""

_IS_HARDWARE = r"""
CREATE OR REPLACE FUNCTION reference_data.telus_is_hardware_detail(p_detail text)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM seeds.telus_hardware_details h
        WHERE h.detail_description = reference_data.telus_detail_signature(p_detail)
    )
$$
"""


def upgrade() -> None:
    op.execute(_SIGNATURE)
    # seeds.telus_hardware_details is built by `dbt seed`, so it does not exist yet.
    # The reference resolves at call time, as reference_data.resolve_bge_alias does.
    op.execute("SET check_function_bodies = off")
    op.execute(_IS_HARDWARE)
    op.execute("RESET check_function_bodies")


def downgrade() -> None:
    # The dbt views go first: their definitions call the signature, and `dbt run`
    # rebuilds them. Named rather than CASCADEd so an unexpected dependent fails loudly.
    op.execute("DROP VIEW IF EXISTS intermediate.int_service_spend_line_items")
    op.execute("DROP VIEW IF EXISTS intermediate.int_telus_ngta_spend")
    op.execute("DROP FUNCTION IF EXISTS reference_data.telus_is_hardware_detail(text)")
    op.execute("DROP FUNCTION IF EXISTS reference_data.telus_detail_signature(text)")
