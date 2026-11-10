"""Add app.user_organizations: the organizations each user is assigned to.

Revision ID: 014_user_organizations
Revises: 013_database_roles
Create Date: 2026-11-10

Org admins and org users only see data for the organizations assigned to them
here. Each row assigns one organization: either a whole BGE (bge_id) or one
sub-BGE / service designee (sub_bge_id), never both. A user can have several
rows. TO admins and TO viewers see all organizations and need no rows.

Only TO admins can manage assignments for now (from the admin page).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_user_organizations"
down_revision: Union[str, None] = "013_database_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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

    # TO admins manage assignments from the admin page. The backend switches to
    # tap_to_admin for the request, so that role needs the schema too.
    op.execute("GRANT USAGE ON SCHEMA app TO tap_to_admin")
    op.execute("GRANT SELECT, INSERT, DELETE ON app.user_organizations TO tap_to_admin")


def downgrade() -> None:
    op.execute("REVOKE ALL ON app.user_organizations FROM tap_to_admin")
    op.execute("REVOKE USAGE ON SCHEMA app FROM tap_to_admin")
    op.drop_index("user_organizations_user_sub_bge_idx", table_name="user_organizations", schema="app")
    op.drop_index("user_organizations_user_bge_idx", table_name="user_organizations", schema="app")
    op.drop_table("user_organizations", schema="app")
