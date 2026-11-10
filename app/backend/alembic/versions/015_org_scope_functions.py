"""Add functions that return the organizations the current user can see.

Revision ID: 015_org_scope_functions
Revises: 014_user_organizations
Create Date: 2026-11-10

The backend will set `tap.user_id` for each request. These functions read the
user's rows in app.user_organizations and return:

- tap_private.allowed_bge_ids(): the BGEs assigned to the user.
- tap_private.allowed_sub_bge_ids(): the sub-BGEs / service designees assigned
  to the user, plus every sub-BGE under them (through parent_sub_bge_id).

Both return an empty array when `tap.user_id` is not set, so a request without
a user sees nothing. Row-level security policies will call them later; nothing
uses them yet.

They run as their owner (SECURITY DEFINER), so the org roles can call them
without being able to read app.user_organizations. search_path is fixed and
every table is schema-qualified, so a caller can't swap in their own tables.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "015_org_scope_functions"
down_revision: Union[str, None] = "014_user_organizations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Group roles from 013_database_roles.
GROUP_ROLES = "tap_to_admin, tap_to_viewer, tap_org_admin, tap_org_user"


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS tap_private")
    op.execute("REVOKE ALL ON SCHEMA tap_private FROM PUBLIC")
    op.execute(f"GRANT USAGE ON SCHEMA tap_private TO {GROUP_ROLES}")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION tap_private.allowed_bge_ids()
        RETURNS integer[]
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = pg_catalog, pg_temp
        AS $$
            SELECT coalesce(array_agg(uo.bge_id), '{}')
              FROM app.user_organizations uo
             WHERE uo.user_id = nullif(current_setting('tap.user_id', true), '')::bigint
               AND uo.bge_id IS NOT NULL
        $$
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION tap_private.allowed_sub_bge_ids()
        RETURNS integer[]
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = pg_catalog, pg_temp
        AS $$
            WITH RECURSIVE allowed AS (
                -- sub-BGEs / service designees assigned to the user
                SELECT uo.sub_bge_id AS id
                  FROM app.user_organizations uo
                 WHERE uo.user_id = nullif(current_setting('tap.user_id', true), '')::bigint
                   AND uo.sub_bge_id IS NOT NULL
                UNION
                -- and everything under them
                SELECT sb.id
                  FROM reference_data.sub_bge sb
                  JOIN allowed a ON sb.parent_sub_bge_id = a.id
            )
            SELECT coalesce(array_agg(id), '{}') FROM allowed
        $$
        """
    )

    # Functions can be run by everyone by default; only the group roles may.
    for function in ["allowed_bge_ids", "allowed_sub_bge_ids"]:
        op.execute(f"REVOKE EXECUTE ON FUNCTION tap_private.{function}() FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION tap_private.{function}() TO {GROUP_ROLES}")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS tap_private.allowed_sub_bge_ids()")
    op.execute("DROP FUNCTION IF EXISTS tap_private.allowed_bge_ids()")
    op.execute("DROP SCHEMA IF EXISTS tap_private")
