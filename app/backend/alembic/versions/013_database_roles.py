"""Database roles for role-based access to data.

Revision ID: 013_database_roles
Revises: 012_drop_session_tokens
Create Date: 2026-11-10

One Postgres role per Entra app role, plus a login user for each part of the
app. Nothing uses them yet: the app still connects as the owner user.

Group roles (no login), named after the Entra app roles:
- tap_to_admin, tap_to_viewer: read `analytics` and `reference_data`.
- tap_org_admin, tap_org_user: no data access yet. Organization-level
  access will be added later.

Login users (passwords are set per environment, not here):
- tap_api: the backend. Reads sessions, then switches to the user's group
  role for each request. NOINHERIT, so it gets no data access by itself.
- tap_web: the frontend. Only the sign-in tables in `app`.

Roles belong to the whole Postgres server, not one database, so they are only
created if they don't exist yet.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "013_database_roles"
down_revision: Union[str, None] = "012_drop_session_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TO_ROLES = ["tap_to_admin", "tap_to_viewer"]
ORG_ROLES = ["tap_org_admin", "tap_org_user"]
GROUP_ROLES = TO_ROLES + ORG_ROLES

DATA_SCHEMAS = ["analytics", "reference_data"]

# What the frontend does to each sign-in table (see frontend/src/lib/server/auth.ts).
WEB_TABLE_GRANTS = {
    "users": "SELECT, INSERT, UPDATE",
    "auth_sessions": "SELECT, INSERT, UPDATE",
    "auth_oauth_states": "SELECT, INSERT, DELETE",
}


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
    for role in GROUP_ROLES:
        _create_role(role, "NOLOGIN")
    _create_role("tap_api", "LOGIN NOINHERIT")
    _create_role("tap_web", "LOGIN")

    # Backend: read sessions, and allowed to switch to any group role.
    op.execute("GRANT USAGE ON SCHEMA app TO tap_api")
    op.execute("GRANT SELECT ON app.auth_sessions TO tap_api")
    op.execute(f"GRANT {', '.join(GROUP_ROLES)} TO tap_api")

    # Frontend: sign-in tables only.
    op.execute("GRANT USAGE ON SCHEMA app TO tap_web")
    for table, privileges in WEB_TABLE_GRANTS.items():
        op.execute(f"GRANT {privileges} ON app.{table} TO tap_web")

    # TO roles read all data. dbt rebuilds the analytics tables on every
    # run, so default privileges also cover tables created later. They apply
    # to tables created by the user running this migration, which is the same
    # user that runs dbt (helm db-migrate-job).
    to_roles = ", ".join(TO_ROLES)
    for schema in DATA_SCHEMAS:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        op.execute(f"GRANT USAGE ON SCHEMA {schema} TO {to_roles}")
        op.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {to_roles}")
        op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO {to_roles}")


def downgrade() -> None:
    to_roles = ", ".join(TO_ROLES)
    for schema in DATA_SCHEMAS:
        op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} REVOKE SELECT ON TABLES FROM {to_roles}")
        op.execute(f"REVOKE SELECT ON ALL TABLES IN SCHEMA {schema} FROM {to_roles}")
        op.execute(f"REVOKE USAGE ON SCHEMA {schema} FROM {to_roles}")

    for table in WEB_TABLE_GRANTS:
        op.execute(f"REVOKE ALL ON app.{table} FROM tap_web")
    op.execute("REVOKE USAGE ON SCHEMA app FROM tap_web")

    op.execute("REVOKE SELECT ON app.auth_sessions FROM tap_api")
    op.execute("REVOKE USAGE ON SCHEMA app FROM tap_api")

    for role in ["tap_api", "tap_web"] + GROUP_ROLES:
        op.execute(f"DROP ROLE IF EXISTS {role}")
