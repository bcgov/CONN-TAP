"""Rename app.users.keycloak_subject to entra_object_id.

Revision ID: 013_users_entra_object_id
Revises: 012_service_sub_category
Create Date: 2026-11-05

Sign-in moves from Keycloak to Entra ID. Users are now identified by their
Entra object ID (the `oid` claim). Rows created through Keycloak keep their
Keycloak subject in this column and will not match an Entra sign-in; those
users get a new row the first time they sign in with Entra.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "013_users_entra_object_id"
down_revision: Union[str, None] = "012_service_sub_category"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "keycloak_subject", new_column_name="entra_object_id", schema="app")


def downgrade() -> None:
    op.alter_column("users", "entra_object_id", new_column_name="keycloak_subject", schema="app")
