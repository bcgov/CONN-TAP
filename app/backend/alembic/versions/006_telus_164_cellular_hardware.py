"""Add a Cellular Hardware category and move Telus service code 164 into it.

Revision ID: 006_telus_164_cellular_hardware
Revises: 005_time_limited_services
Create Date: 2026-08-28

Telus ngta source_id 164 was mapped to the Cellular category alongside 130,
but recent guidance is that 164 identifies hardware charges (device
purchases/easy-payment lines), not cellular plan spend. This adds a
dedicated Cellular Hardware category and remaps 164 onto it, matching the
cellular_hardware / cellular_plans split already used by the Telus spend
report script (scripts/sql/telus.sql).

As with 005, the fact table stores the resolved service_category_id, so
existing spend needs a dbt run to move into the new category; this
migration only changes where new resolutions land.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "006_telus_164_cellular_hardware"
down_revision: Union[str, None] = "005_time_limited_services"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO reference_data.service_category (code, name)
        VALUES ('cellular_hardware', 'Cellular Hardware')
        ON CONFLICT (code) DO NOTHING
        """
    )
    op.execute(_remap("cellular_hardware", "('ngta', '164')"))


def downgrade() -> None:
    op.execute(_remap("cellular", "('ngta', '164')"))
    # Only droppable once nothing points at it, so this trails the remap.
    # Any analytics rows still referencing it need a dbt run to move off first.
    op.execute("DELETE FROM reference_data.service_category WHERE code = 'cellular_hardware'")


def _remap(category_code: str, source_code_pairs: str) -> str:
    """Point the given (source_system, code) service codes at a category.

    Both arguments are literals written in this file — no external input.
    """
    return f"""
        UPDATE reference_data.service_code sc
        SET service_category_id = cat.id, updated_at = now()
        FROM reference_data.service_category cat
        WHERE cat.code = '{category_code}'
          AND (sc.source_system, sc.code) IN ({source_code_pairs})
    """
