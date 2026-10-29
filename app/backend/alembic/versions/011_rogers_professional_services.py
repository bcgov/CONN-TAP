"""Add the Rogers service code professional_services, mapped to Professional Services.

Revision ID: 011_rogers_professional_services
Revises: 010_rogers_cellular_hardware
Create Date: 2026-10-23

int_rogers_ngta_spend now takes a Rogers line's service code from the pricebook its
service ID is listed in. The Professional Services pricebook gives the code
professional_services, mapped here to the existing Professional Services category
(migration 005).

As with 005, 006, 009 and 010, existing spend needs a dbt run to move.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "011_rogers_professional_services"
down_revision: Union[str, None] = "010_rogers_cellular_hardware"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO reference_data.service_code
            (source_system, provider_id, code, service_category_id, service_name)
        SELECT 'ngta', p.id, 'professional_services', sc.id, 'Professional Services'
        FROM reference_data.provider p
        JOIN reference_data.service_category sc ON sc.code = 'professional_services'
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
        WHERE source_system = 'ngta' AND code = 'professional_services'
        """
    )
