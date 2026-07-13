"""Initial app schema: users, auth_sessions, auth_oauth_states.

Revision ID: 001_initial_app_schema
Revises:
Create Date: 2026-05-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_app_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS app")

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("keycloak_subject", sa.Text(), nullable=False),
        sa.Column("username", sa.Text(), nullable=True),
        sa.Column("given_name", sa.Text(), nullable=True),
        sa.Column("family_name", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("keycloak_subject"),
        schema="app",
    )

    op.create_table(
        "auth_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("session_hash", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("username", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column(
            "claims",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("encrypted_access_token", sa.Text(), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=True),
        sa.Column("encrypted_id_token", sa.Text(), nullable=True),
        sa.Column("access_token_hash", sa.Text(), nullable=False),
        sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["app.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_hash"),
        schema="app",
    )
    op.create_index(
        "auth_sessions_session_hash_idx",
        "auth_sessions",
        ["session_hash"],
        unique=False,
        schema="app",
    )
    op.create_index(
        "auth_sessions_subject_idx",
        "auth_sessions",
        ["subject"],
        unique=False,
        schema="app",
    )
    op.create_index(
        "auth_sessions_expires_idx",
        "auth_sessions",
        ["session_expires_at"],
        unique=False,
        schema="app",
    )

    op.create_table(
        "auth_oauth_states",
        sa.Column("state_hash", sa.Text(), nullable=False),
        sa.Column("pkce_verifier", sa.Text(), nullable=False),
        sa.Column("nonce", sa.Text(), nullable=False),
        sa.Column("return_to", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("state_hash"),
        schema="app",
    )
    op.create_index(
        "auth_oauth_states_expires_idx",
        "auth_oauth_states",
        ["expires_at"],
        unique=False,
        schema="app",
    )


def downgrade() -> None:
    op.drop_index("auth_oauth_states_expires_idx", table_name="auth_oauth_states", schema="app")
    op.drop_table("auth_oauth_states", schema="app")
    op.drop_index("auth_sessions_expires_idx", table_name="auth_sessions", schema="app")
    op.drop_index("auth_sessions_subject_idx", table_name="auth_sessions", schema="app")
    op.drop_index("auth_sessions_session_hash_idx", table_name="auth_sessions", schema="app")
    op.drop_table("auth_sessions", schema="app")
    op.drop_table("users", schema="app")
    op.execute("DROP SCHEMA IF EXISTS app CASCADE")
