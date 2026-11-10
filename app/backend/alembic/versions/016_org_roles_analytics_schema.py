"""Let the org roles reach the analytics schema.

Revision ID: 016_org_roles_analytics_schema
Revises: 015_org_scope_functions
Create Date: 2026-11-10

Only schema access. Org roles get SELECT on single analytics tables from the
dbt post-hook org_row_security, which also adds the row-level security that
limits them to their assigned organizations. Tables without that post-hook
stay closed to them.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "016_org_roles_analytics_schema"
down_revision: Union[str, None] = "015_org_scope_functions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ORG_ROLES = "tap_org_admin, tap_org_user"


def upgrade() -> None:
    op.execute(f"GRANT USAGE ON SCHEMA analytics TO {ORG_ROLES}")


def downgrade() -> None:
    op.execute(f"REVOKE USAGE ON SCHEMA analytics FROM {ORG_ROLES}")
