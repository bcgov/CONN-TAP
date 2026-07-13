"""SQLAlchemy session and engine."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Pin search_path as a libpq *startup* option so it applies to every connection
# and survives the pool's reset-on-return ROLLBACK. A post-connect `SET` is not
# reliable: it is reverted when SQLAlchemy rolls back the connection on return,
# after which an unqualified `auth_sessions` resolves via the role default
# search_path (e.g. `public` for the `dbadmin` role) and can hit a stale shadow
# table instead of `app.auth_sessions`.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
    connect_args={"options": "-c search_path=app,public"},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
