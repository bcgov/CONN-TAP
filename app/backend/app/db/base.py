"""SQLAlchemy declarative bases. Kept free of model imports to avoid cycles."""
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Default base for tables in the public schema (e.g. datasets registry)."""
    pass


class AppBase(DeclarativeBase):
    """Base for application tables in the Postgres `app` schema (auth, users)."""
    metadata = MetaData(schema="app")
