"""SQLAlchemy declarative base. Kept free of model imports to avoid cycles."""
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class AppBase(DeclarativeBase):
    """Base for all application tables, in the Postgres `app` schema.

    Everything lives in `app` so that no object resolves via the public schema;
    this avoids search_path ambiguity entirely.
    """
    metadata = MetaData(schema="app")
