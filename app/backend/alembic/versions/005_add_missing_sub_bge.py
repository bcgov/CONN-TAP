"""Add Gov BC sub-orgs that landed after 004 was already applied in existing envs.

These five sub-orgs were originally appended to sub_bge.sql (PR #58 / commit
c88362e), but migration 004 — which loads sub_bge.sql — was already applied in
existing environments, so they never got inserted there. They now live in this
migration instead of sub_bge.sql, so a new revision actually applies them on the
next `alembic upgrade`. INSERT ... ON CONFLICT DO NOTHING keeps it safe where the
rows already exist.

Revision ID: 005_add_missing_sub_bge
Revises: 004_reference_data_schema
Create Date: 2026-07-09

"""
from typing import Sequence, Union

from alembic import op

revision: str = "005_add_missing_sub_bge"
down_revision: Union[str, Sequence[str], None] = "004_reference_data_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Gov BC sub-orgs added after 004. (code == name for all five.)
_ADDED_SUB_BGE_CODES = (
    "Agriculture and Food",
    "Children and Family Development",
    "Mining and Critical Minerals",
    "Public Safety and Solicitor General",
    "Water Land and Resource Stewardship",
)


def upgrade() -> None:
    values = ",\n    ".join(
        f"('{code}', '{code}', (SELECT id FROM reference_data.bge WHERE code = 'Gov BC'), 'sub_org')"
        for code in _ADDED_SUB_BGE_CODES
    )
    op.execute(
        "INSERT INTO reference_data.sub_bge (code, name, bge_id, entity_type) VALUES\n    "
        + values
        + "\nON CONFLICT (code) DO NOTHING"
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM reference_data.sub_bge WHERE code IN ("
        + ", ".join(f"'{code}'" for code in _ADDED_SUB_BGE_CODES)
        + ")"
    )
