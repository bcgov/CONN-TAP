"""TAP roles: the Entra app roles and the Postgres role each one uses."""
from __future__ import annotations

GLOBAL_ADMIN = "global_admin"
GLOBAL_ANALYST = "global_analyst"
ORG_ADMIN = "org_admin"
ORG_ANALYST = "org_analyst"

# Postgres role for each Entra app role (created in alembic 013_database_roles),
# highest first. A user with several roles gets the first one that matches.
DATABASE_ROLES = {
    GLOBAL_ADMIN: "tap_global_admin",
    GLOBAL_ANALYST: "tap_global_analyst",
    ORG_ADMIN: "tap_org_admin",
    ORG_ANALYST: "tap_org_analyst",
}


def database_role(roles: list[str]) -> str | None:
    """The Postgres role for a user's Entra roles, or None if they have no TAP role."""
    for app_role, db_role in DATABASE_ROLES.items():
        if app_role in roles:
            return db_role
    return None
