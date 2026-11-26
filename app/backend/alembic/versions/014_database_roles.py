"""Database roles and organization-level access to data.

Revision ID: 014_database_roles
Revises: 013_entra_sign_in
Create Date: 2026-11-10

Roles. Roles belong to the whole Postgres server, not one database, so they
are only created if they don't exist yet.

- Group roles (no login), named after the Entra app roles:
  - tap_to_admin, tap_to_viewer: read all of `analytics` and `reference_data`.
  - tap_org_admin, tap_org_user: only the organizations assigned to them.
- Login users (passwords are set per environment, not here):
  - tap_api: the backend. Reads sessions, then switches to the user's group
    role for each request. NOINHERIT, so it gets no data access by itself.
  - tap_web: the frontend. The sign-in tables, organization assignments, and
    organization names (for the dashboards and the admin page). No spend data.

app.user_organizations: the organizations each user is assigned to. Each row
assigns one organization: either a whole BGE (bge_id) or one sub-BGE / service
designee (sub_bge_id), never both. TO admins and TO viewers see all
organizations and need no rows. Only TO admins manage assignments for now
(from the admin page).

tap_private functions return the organizations the current user can see. The
backend sets `tap.user_id` for each request; without it they return an empty
array, so a request without a user sees nothing.
- allowed_bge_ids(): the BGEs assigned to the user.
- allowed_sub_bge_ids(): the sub-BGEs / service designees assigned to the
  user, plus every sub-BGE under them (through parent_sub_bge_id).
They run as their owner (SECURITY DEFINER), so the org roles can call them
without being able to read app.user_organizations. search_path is fixed and
every table is schema-qualified, so a caller can't swap in their own tables.

Org roles and reference data. Org datasets join analytics tables to
reference_data.bge / sub_bge for names and the org hierarchy. Org roles get:
- sector, provider, service_category: all rows. Plain lookup lists.
- bge, sub_bge: only their own organizations, through row-level security.
  - bge: their assigned BGEs, plus the parent BGE of each assigned sub-BGE
    (only the name; the queries inner join on it).
  - sub_bge: everything under their assigned BGEs, and their assigned
    sub-BGEs / service designees and everything under them.
- analytics: schema access only. SELECT on single analytics tables, and the
  row-level security that limits them, come from the dbt post-hook
  org_row_security. Tables without that post-hook stay closed to them.
TO roles and tap_web see every bge / sub_bge row. The table owner (alembic,
dbt) is not affected by row-level security.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_database_roles"
down_revision: Union[str, None] = "013_entra_sign_in"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TO_ROLES = ["tap_to_admin", "tap_to_viewer"]
ORG_ROLES = ["tap_org_admin", "tap_org_user"]
GROUP_ROLES = TO_ROLES + ORG_ROLES

DATA_SCHEMAS = ["analytics", "reference_data"]

# What the frontend does to each table in `app` (see
# frontend/src/lib/server/auth.ts and user-organizations.ts).
WEB_TABLE_GRANTS = {
    "users": "SELECT, INSERT, UPDATE",
    "auth_sessions": "SELECT, INSERT, UPDATE",
    "auth_oauth_states": "SELECT, INSERT, DELETE",
    "user_organizations": "SELECT, INSERT, DELETE",
}

# Reference tables the org roles can read. bge and sub_bge are limited to their
# own organizations by row-level security.
ORG_REFERENCE_TABLES = ["sector", "provider", "service_category", "bge", "sub_bge"]
ORGANIZATION_TABLES = ["bge", "sub_bge"]


def _create_role(name: str, options: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{name}') THEN
                CREATE ROLE {name} {options};
            END IF;
        END
        $$
        """
    )


def upgrade() -> None:
    to_roles = ", ".join(TO_ROLES)
    org_roles = ", ".join(ORG_ROLES)
    group_roles = ", ".join(GROUP_ROLES)

    # --- Roles ---
    for role in GROUP_ROLES:
        _create_role(role, "NOLOGIN")
    _create_role("tap_api", "LOGIN NOINHERIT")
    _create_role("tap_web", "LOGIN")

    # --- app.user_organizations ---
    op.create_table(
        "user_organizations",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("bge_id", sa.Integer(), nullable=True),
        sa.Column("sub_bge_id", sa.Integer(), nullable=True),
        sa.Column("assigned_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["app.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bge_id"], ["reference_data.bge.id"]),
        sa.ForeignKeyConstraint(["sub_bge_id"], ["reference_data.sub_bge.id"]),
        sa.ForeignKeyConstraint(["assigned_by"], ["app.users.id"], ondelete="SET NULL"),
        # Exactly one of bge_id / sub_bge_id is set.
        sa.CheckConstraint(
            "(bge_id IS NULL) <> (sub_bge_id IS NULL)",
            name="user_organizations_one_org",
        ),
        schema="app",
    )

    # The same organization can't be assigned to a user twice. Two partial
    # indexes because the column that isn't used is NULL.
    op.create_index(
        "user_organizations_user_bge_idx",
        "user_organizations",
        ["user_id", "bge_id"],
        unique=True,
        schema="app",
        postgresql_where=sa.text("bge_id IS NOT NULL"),
    )
    op.create_index(
        "user_organizations_user_sub_bge_idx",
        "user_organizations",
        ["user_id", "sub_bge_id"],
        unique=True,
        schema="app",
        postgresql_where=sa.text("sub_bge_id IS NOT NULL"),
    )

    # --- Backend: read sessions, and allowed to switch to any group role ---
    op.execute("GRANT USAGE ON SCHEMA app TO tap_api")
    op.execute("GRANT SELECT ON app.auth_sessions TO tap_api")
    op.execute(f"GRANT {group_roles} TO tap_api")

    # --- Frontend: sign-in tables, organization assignments and names ---
    op.execute("GRANT USAGE ON SCHEMA app TO tap_web")
    for table, privileges in WEB_TABLE_GRANTS.items():
        op.execute(f"GRANT {privileges} ON app.{table} TO tap_web")
    op.execute("GRANT USAGE ON SCHEMA reference_data TO tap_web")
    for table in ORGANIZATION_TABLES:
        op.execute(f"GRANT SELECT ON reference_data.{table} TO tap_web")

    # --- TO roles read all data ---
    # dbt rebuilds the analytics tables on every run, so default privileges
    # also cover tables created later. They apply to tables created by the user
    # running this migration, which is the same user that runs dbt
    # (helm db-migrate-job).
    for schema in DATA_SCHEMAS:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO {to_roles}")
        op.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {to_roles}")
        op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO {to_roles}")

    # TO admins manage assignments from the admin page. The backend switches to
    # tap_to_admin for the request, so that role needs the schema too.
    op.execute("GRANT USAGE ON SCHEMA app TO tap_to_admin")
    op.execute("GRANT SELECT, INSERT, DELETE ON app.user_organizations TO tap_to_admin")

    # --- Functions: the organizations the current user can see ---
    op.execute("CREATE SCHEMA IF NOT EXISTS tap_private")
    op.execute("REVOKE ALL ON SCHEMA tap_private FROM PUBLIC")
    op.execute(f"GRANT USAGE ON SCHEMA tap_private TO {group_roles}")

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
        op.execute(f"GRANT EXECUTE ON FUNCTION tap_private.{function}() TO {group_roles}")

    # --- Org roles: analytics schema and reference data ---
    op.execute(f"GRANT USAGE ON SCHEMA analytics TO {org_roles}")

    op.execute(f"GRANT USAGE ON SCHEMA reference_data TO {org_roles}")
    for table in ORG_REFERENCE_TABLES:
        op.execute(f"GRANT SELECT ON reference_data.{table} TO {org_roles}")

    # --- Row-level security on bge / sub_bge ---
    # (select ...) runs the function once per query, not per row. The
    # ::integer[] cast makes ANY compare against the array's items.
    op.execute("ALTER TABLE reference_data.bge ENABLE ROW LEVEL SECURITY")
    op.execute(f"CREATE POLICY to_all ON reference_data.bge FOR SELECT TO {to_roles} USING (true)")
    op.execute("CREATE POLICY web_all ON reference_data.bge FOR SELECT TO tap_web USING (true)")
    op.execute(
        f"""
        CREATE POLICY org_scope ON reference_data.bge
            FOR SELECT
            TO {org_roles}
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
    op.execute(f"CREATE POLICY to_all ON reference_data.sub_bge FOR SELECT TO {to_roles} USING (true)")
    op.execute("CREATE POLICY web_all ON reference_data.sub_bge FOR SELECT TO tap_web USING (true)")
    op.execute(
        f"""
        CREATE POLICY org_scope ON reference_data.sub_bge
            FOR SELECT
            TO {org_roles}
            USING (
                bge_id = ANY ((SELECT tap_private.allowed_bge_ids())::integer[])
                OR id = ANY ((SELECT tap_private.allowed_sub_bge_ids())::integer[])
            )
        """
    )


def downgrade() -> None:
    to_roles = ", ".join(TO_ROLES)
    org_roles = ", ".join(ORG_ROLES)

    # --- Row-level security on bge / sub_bge ---
    for table in ORGANIZATION_TABLES:
        op.execute(f"DROP POLICY IF EXISTS org_scope ON reference_data.{table}")
        op.execute(f"DROP POLICY IF EXISTS web_all ON reference_data.{table}")
        op.execute(f"DROP POLICY IF EXISTS to_all ON reference_data.{table}")
        op.execute(f"ALTER TABLE reference_data.{table} DISABLE ROW LEVEL SECURITY")

    # --- Org roles: analytics schema and reference data ---
    for table in ORG_REFERENCE_TABLES:
        op.execute(f"REVOKE SELECT ON reference_data.{table} FROM {org_roles}")
    op.execute(f"REVOKE USAGE ON SCHEMA reference_data FROM {org_roles}")
    op.execute(f"REVOKE USAGE ON SCHEMA analytics FROM {org_roles}")

    # --- Functions ---
    op.execute("DROP FUNCTION IF EXISTS tap_private.allowed_sub_bge_ids()")
    op.execute("DROP FUNCTION IF EXISTS tap_private.allowed_bge_ids()")
    op.execute("DROP SCHEMA IF EXISTS tap_private")

    # --- TO roles ---
    op.execute("REVOKE USAGE ON SCHEMA app FROM tap_to_admin")
    for schema in DATA_SCHEMAS:
        op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} REVOKE SELECT ON TABLES FROM {to_roles}")
        op.execute(f"REVOKE SELECT ON ALL TABLES IN SCHEMA {schema} FROM {to_roles}")
        op.execute(f"REVOKE USAGE ON SCHEMA {schema} FROM {to_roles}")

    # --- Frontend ---
    for table in ORGANIZATION_TABLES:
        op.execute(f"REVOKE SELECT ON reference_data.{table} FROM tap_web")
    op.execute("REVOKE USAGE ON SCHEMA reference_data FROM tap_web")
    for table in WEB_TABLE_GRANTS:
        op.execute(f"REVOKE ALL ON app.{table} FROM tap_web")
    op.execute("REVOKE USAGE ON SCHEMA app FROM tap_web")

    # --- Backend ---
    op.execute("REVOKE SELECT ON app.auth_sessions FROM tap_api")
    op.execute("REVOKE USAGE ON SCHEMA app FROM tap_api")

    # --- app.user_organizations (its grants and indexes go with it) ---
    op.drop_table("user_organizations", schema="app")

    # --- Roles ---
    for role in ["tap_api", "tap_web"] + GROUP_ROLES:
        op.execute(f"DROP ROLE IF EXISTS {role}")
