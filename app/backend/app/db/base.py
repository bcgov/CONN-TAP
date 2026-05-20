"""SQLAlchemy declarative base. Kept free of model imports to avoid cycles."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
