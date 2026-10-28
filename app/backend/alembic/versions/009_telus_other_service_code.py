"""Add the TELUS fallback service code telus_other, mapped to Unknown.

Revision ID: 009_telus_other_service_code
Revises: 008_historic_old_pricebooks
Create Date: 2026-10-14

The spend report (scripts/sql/telus.sql) puts a TELUS row that isn't Wireless
and has a blank or unconfirmed source_id into Other. dbt left those rows with a
null category. int_telus_ngta_spend now resolves them to 'telus_other', which
this maps to the existing Unknown category (migration 005).

TELUS can't reuse Rogers' 'other' code: service_code is unique on
(source_system, code) and both providers use 'ngta'.

As with 005 and 006, existing spend needs a dbt run to move.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "009_telus_other_service_code"
down_revision: Union[str, None] = "008_historic_old_pricebooks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO reference_data.service_code
            (source_system, provider_id, code, service_category_id, service_name)
        SELECT 'ngta', p.id, 'telus_other', sc.id, 'Other'
        FROM reference_data.provider p
        JOIN reference_data.service_category sc ON sc.code = 'unknown'
        WHERE p.code = 'telus'
        ON CONFLICT (source_system, code) DO NOTHING
        """
    )


def downgrade() -> None:
    # Removes only the row upgrade() added. Spend resolved through it needs a
    # dbt run to move off it.
    op.execute(
        """
        DELETE FROM reference_data.service_code
        WHERE source_system = 'ngta' AND code = 'telus_other'
        """
    )
