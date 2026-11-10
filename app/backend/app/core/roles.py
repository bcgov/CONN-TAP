"""TAP roles: the Entra app roles and the Postgres role each one uses."""
from __future__ import annotations

TO_ADMIN = "to_admin"
TO_VIEWER = "to_viewer"
ORG_ADMIN = "org_admin"
ORG_USER = "org_user"

# Postgres role for each Entra app role (created in alembic 013_database_roles),
# highest first. A user with several roles gets the first one that matches.
DATABASE_ROLES = {
    TO_ADMIN: "tap_to_admin",
    TO_VIEWER: "tap_to_viewer",
    ORG_ADMIN: "tap_org_admin",
    ORG_USER: "tap_org_user",
}


def database_role(roles: list[str]) -> str | None:
    """The Postgres role for a user's Entra roles, or None if they have no TAP role."""
    for app_role, db_role in DATABASE_ROLES.items():
        if app_role in roles:
            return db_role
    return None
