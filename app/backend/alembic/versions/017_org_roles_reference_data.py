"""Let the org roles read reference data, limited to their own organizations.

Revision ID: 017_org_roles_reference_data
Revises: 016_org_roles_analytics_schema
Create Date: 2026-11-10

Org datasets join analytics tables to reference_data.bge / sub_bge for names
and the org hierarchy. Org roles get:

- sector, provider, service_category: all rows. Plain lookup lists, nothing
  organization specific.
- bge, sub_bge: only their own organizations, through row-level security.
  - bge: their assigned BGEs, plus the parent BGE of each assigned sub-BGE
    (only the name; the queries inner join on it).
  - sub_bge: everything under their assigned BGEs, and their assigned
    sub-BGEs / service designees and everything under them.

TO roles keep seeing every row. The table owner (alembic, dbt) is not
affected by row-level security.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "017_org_roles_reference_data"
down_revision: Union[str, None] = "016_org_roles_analytics_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TO_ROLES = "tap_to_admin, tap_to_viewer"
ORG_ROLES = "tap_org_admin, tap_org_user"

ORG_TABLES = ["sector", "provider", "service_category", "bge", "sub_bge"]


def upgrade() -> None:
    op.execute(f"GRANT USAGE ON SCHEMA reference_data TO {ORG_ROLES}")
    for table in ORG_TABLES:
        op.execute(f"GRANT SELECT ON reference_data.{table} TO {ORG_ROLES}")

    # (select ...) runs the function once per query, not per row. The
    # ::integer[] cast makes ANY compare against the array's items.
    op.execute("ALTER TABLE reference_data.bge ENABLE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY to_all ON reference_data.bge FOR SELECT TO {TO_ROLES} USING (true)")
    op.execute(
        f"""
        CREATE POLICY org_scope ON reference_data.bge
            FOR SELECT
            TO {ORG_ROLES}
            USING (
                id = ANY ((SELECT tap_private.allowed_bge_ids())::integer[])
                OR id IN (
                    SELECT sb.bge_id
                      FROM reference_data.sub_bge sb
                     WHERE sb.id = ANY ((SELECT tap_private.allowed_sub_bge_ids())::integer[])
                )
            )
        """
    )

    op.execute("ALTER TABLE reference_data.sub_bge ENABLE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY to_all ON reference_data.sub_bge FOR SELECT TO {TO_ROLES} USING (true)")
    op.execute(
        f"""
        CREATE POLICY org_scope ON reference_data.sub_bge
            FOR SELECT
            TO {ORG_ROLES}
            USING (
                bge_id = ANY ((SELECT tap_private.allowed_bge_ids())::integer[])
                OR id = ANY ((SELECT tap_private.allowed_sub_bge_ids())::integer[])
            )
        """
    )


def downgrade() -> None:
    for table in ["bge", "sub_bge"]:
        op.execute(f"DROP POLICY IF EXISTS org_scope ON reference_data.{table}")
        op.execute(f"DROP POLICY IF EXISTS to_all ON reference_data.{table}")
        op.execute(f"ALTER TABLE reference_data.{table} DISABLE ROW LEVEL SECURITY")

    for table in ORG_TABLES:
        op.execute(f"REVOKE SELECT ON reference_data.{table} FROM {ORG_ROLES}")
    op.execute(f"REVOKE USAGE ON SCHEMA reference_data FROM {ORG_ROLES}")
