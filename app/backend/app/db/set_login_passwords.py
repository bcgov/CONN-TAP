"""Set the passwords of the app's database login users.

tap_api (backend) and tap_web (frontend) are created without passwords by
alembic 013_database_roles. The deploy's migrate job runs this after the
migrations, as the owner user, with the passwords from Secrets Manager, so
Postgres always matches Secrets Manager. Locally the variables are not set and
nothing changes.

    python -m app.db.set_login_passwords
"""
import os

import psycopg
from psycopg import sql

from app.core.config import settings

LOGIN_USERS = {
    "tap_api": "TAP_API_POSTGRES_PASSWORD",
    "tap_web": "TAP_WEB_POSTGRES_PASSWORD",
}


def main() -> None:
    with psycopg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB,
        sslmode="require" if settings.POSTGRES_SSL else "disable",
    ) as conn:
        for user, variable in LOGIN_USERS.items():
            password = os.environ.get(variable)
            if not password:
                print(f"No password given for {user}; left unchanged")
                continue
            # ALTER ROLE can't take a bind parameter, so the password is quoted as a literal.
            conn.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(sql.Identifier(user), sql.Literal(password)))
            print(f"Updated {user}")


if __name__ == "__main__":
    main()
