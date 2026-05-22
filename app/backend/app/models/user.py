"""Application user identity (Keycloak subject), not local credentials."""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import AppBase


class User(AppBase):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    keycloak_subject: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    username: Mapped[str | None] = mapped_column(Text)
    given_name: Mapped[str | None] = mapped_column(Text)
    family_name: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    display_name: Mapped[str | None] = mapped_column(Text)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
