"""FastAPI dependencies for the session shared with Next.js."""
from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from typing import Any

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db


@dataclass(frozen=True)
class AuthenticatedUser:
    subject: str
    username: str | None
    email: str | None
    name: str | None
    claims: dict[str, Any]
    roles: list[str]

    def has_any_role(self, required_roles: tuple[str, ...]) -> bool:
        if not required_roles:
            return True
        return any(role in self.roles for role in required_roles)


def _secret_bytes(value: str, min_bytes: int = 32) -> bytes:
    try:
        decoded = base64.b64decode(value, validate=True)
        if len(decoded) >= min_bytes:
            return decoded
    except Exception:
        pass

    raw = value.encode()
    if len(raw) >= min_bytes:
        return raw

    raise RuntimeError("SESSION_SECRET must be base64 encoded or raw text with at least 32 bytes")


def _base64url_digest(digest: bytes) -> str:
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

def hash_session_token(token: str) -> str:
    return _base64url_digest(hmac.new(_secret_bytes(settings.SESSION_SECRET), token.encode(), hashlib.sha256).digest())

def _unauthorized(detail: str = "Unauthorized") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def get_current_user(
    session_cookie: str | None = Cookie(default=None, alias=settings.SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """Look up the session created by Next.js at sign-in. The session cookie is
    only usable if its hash matches an active row in auth_sessions."""
    if not session_cookie:
        raise _unauthorized()

    row = (
        db.execute(
            text(
                """
                SELECT subject, username, email, name, claims
                  FROM auth_sessions
                 WHERE session_hash = :session_hash
                   AND revoked_at IS NULL
                   AND session_expires_at > now()
                """
            ),
            {"session_hash": hash_session_token(session_cookie)},
        )
        .mappings()
        .first()
    )

    if row is None:
        raise _unauthorized("Invalid session")

    claims = row["claims"] or {}
    # Entra app roles assigned to the user arrive in the `roles` claim.
    claim_roles = claims.get("roles")
    roles = [r for r in claim_roles if isinstance(r, str)] if isinstance(claim_roles, list) else []

    return AuthenticatedUser(
        subject=row["subject"],
        username=row["username"],
        email=row["email"],
        name=row["name"],
        claims=claims,
        roles=roles,
    )
