"""Add the Rogers service code cellular_hardware, mapped to Cellular Hardware.

Revision ID: 010_rogers_cellular_hardware
Revises: 009_telus_other_service_code
Create Date: 2026-10-18

The spend report (scripts/sql/rogers.sql) splits each Rogers cellular row into
Cellular H/W (`hardware`) and Cellular Plans (`billed_amount_pre_tax - hardware`).
dbt booked the whole billed amount as `cellular`. int_rogers_ngta_spend now emits
the hardware part as its own line with this code, mapped to the existing
Cellular Hardware category (migration 006).

As with 005, 006 and 009, existing spend needs a dbt run to move.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "010_rogers_cellular_hardware"
down_revision: Union[str, None] = "009_telus_other_service_code"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO reference_data.service_code
            (source_system, provider_id, code, service_category_id, service_name)
        SELECT 'ngta', p.id, 'cellular_hardware', sc.id, 'Cellular Hardware'
        FROM reference_data.provider p
        JOIN reference_data.service_category sc ON sc.code = 'cellular_hardware'
        WHERE p.code = 'rogers'
        ON CONFLICT (source_system, code) DO NOTHING
        """
    )


def downgrade() -> None:
    # Removes only the row upgrade() added. Spend resolved through it needs a
    # dbt run to move off it.
    op.execute(
        """
        DELETE FROM reference_data.service_code
        WHERE source_system = 'ngta' AND code = 'cellular_hardware'
        """
    )
