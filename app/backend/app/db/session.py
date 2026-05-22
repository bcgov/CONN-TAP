"""SQLAlchemy session and engine."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@event.listens_for(engine, "connect")
def _set_search_path(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("SET search_path TO app, public")
    cursor.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
