"""Alembic environment for the Postgres `app` schema (database `app`)."""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

from app.core.config import settings
from app.db.base import AppBase
from app.models import auth, user  # noqa: F401 — register models on AppBase.metadata

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = AppBase.metadata


def _ensure_app_schema(connection) -> None:
    """Create schema before Alembic creates app.alembic_version (runs before revisions)."""
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS app"))
    connection.commit()


def _migration_engine():
    return engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )


def run_migrations_offline() -> None:
    with _migration_engine().connect() as connection:
        _ensure_app_schema(connection)

    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="app",
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with _migration_engine().connect() as connection:
        _ensure_app_schema(connection)

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="app",
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
