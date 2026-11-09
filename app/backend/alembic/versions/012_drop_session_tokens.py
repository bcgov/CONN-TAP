"""Drop the stored tokens from app.auth_sessions.

Revision ID: 012_drop_session_tokens
Revises: 011_users_entra_object_id
Create Date: 2026-11-05

With Entra, TAP only needs the ID token at sign-in: its claims (user details
and roles) are saved on the session row. The access, refresh and ID tokens
were stored for Keycloak token checks and refresh, which are gone.

Existing sessions are deleted: they were created through Keycloak and cannot
be used with Entra. Users sign in again.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012_drop_session_tokens"
down_revision: Union[str, None] = "011_users_entra_object_id"
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
