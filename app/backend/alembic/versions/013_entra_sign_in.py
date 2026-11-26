"""Sign-in moves from Keycloak to Entra ID.

Revision ID: 013_entra_sign_in
Revises: 012_service_sub_category
Create Date: 2026-11-05

- app.users.keycloak_subject is renamed to entra_object_id. Users are now
  identified by their Entra object ID (the `oid` claim). Rows created through
  Keycloak keep their Keycloak subject in this column and will not match an
  Entra sign-in; those users get a new row the first time they sign in with
  Entra.
- The stored tokens are dropped from app.auth_sessions. With Entra, TAP only
  needs the ID token at sign-in: its claims (user details and roles) are saved
  on the session row. The access, refresh and ID tokens were stored for
  Keycloak token checks and refresh, which are gone. Existing sessions are
  deleted: they were created through Keycloak and cannot be used with Entra.
  Users sign in again.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_entra_sign_in"
down_revision: Union[str, None] = "012_service_sub_category"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TOKEN_COLUMNS = [
    "encrypted_access_token",
    "encrypted_refresh_token",
    "encrypted_id_token",
    "access_token_hash",
    "access_token_expires_at",
]


def upgrade() -> None:
    op.alter_column("users", "keycloak_subject", new_column_name="entra_object_id", schema="app")

    op.execute("DELETE FROM app.auth_sessions")
    for column in TOKEN_COLUMNS:
        op.drop_column("auth_sessions", column, schema="app")


def downgrade() -> None:
    # Sessions created without tokens cannot be filled in; remove them so the
    # NOT NULL columns can be added back.
    op.execute("DELETE FROM app.auth_sessions")
    op.add_column("auth_sessions", sa.Column("encrypted_access_token", sa.Text(), nullable=False), schema="app")
    op.add_column("auth_sessions", sa.Column("encrypted_refresh_token", sa.Text(), nullable=True), schema="app")
    op.add_column("auth_sessions", sa.Column("encrypted_id_token", sa.Text(), nullable=True), schema="app")
    op.add_column("auth_sessions", sa.Column("access_token_hash", sa.Text(), nullable=False), schema="app")
    op.add_column(
        "auth_sessions",
        sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=False),
        schema="app",
    )

    op.alter_column("users", "entra_object_id", new_column_name="keycloak_subject", schema="app")
