"""Move the School Districts BGE under the Gov & ECC sector.

Revision ID: 006_update_school_sector
Revises: 005_add_missing_sub_bge
Create Date: 2026-07-03

"""
from typing import Sequence, Union

from alembic import op

revision: str = "006_update_school_sector"
down_revision: Union[str, Sequence[str], None] = "005_add_missing_sub_bge"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE reference_data.bge
        SET sector_id = (SELECT id FROM reference_data.sector WHERE code = 'gov_ecc')
        WHERE code = 'School Districts'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE reference_data.bge
        SET sector_id = (SELECT id FROM reference_data.sector WHERE code = 'school_districts')
        WHERE code = 'School Districts'
        """
    )
