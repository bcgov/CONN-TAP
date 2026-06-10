"""FastAPI dependencies for shared Next.js/Keycloak sessions."""
from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import jwt
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)
_jwks_client: PyJWKClient | None = None


@dataclass(frozen=True)
class AuthenticatedUser:
    subject: str
    username: str | None
    email: str | None
    name: str | None
    claims: dict[str, Any]


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

def hash_access_token(token: str) -> str:
    return _base64url_digest(hashlib.sha256(token.encode()).digest())

def jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(f"{settings.KEYCLOAK_ISSUER_URL.rstrip('/')}/protocol/openid-connect/certs")
    return _jwks_client

def _unauthorized(detail: str = "Unauthorized") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _validate_token(token: str) -> dict[str, Any]:
    try:
        signing_key = jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.KEYCLOAK_ISSUER_URL.rstrip("/"),
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise _unauthorized("Invalid access token") from exc

    audience = claims.get("aud")
    audiences = audience if isinstance(audience, list) else [audience]
    authorized_party = claims.get("azp")
    if settings.KEYCLOAK_CLIENT_ID not in audiences and authorized_party != settings.KEYCLOAK_CLIENT_ID:
        raise _unauthorized("Invalid token audience")

    return claims


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session_cookie: str | None = Cookie(default=None, alias=settings.SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    if not session_cookie or credentials is None:
        raise _unauthorized()

    token = credentials.credentials
    claims = _validate_token(token)
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise _unauthorized("Token is missing subject")

    row = (
        db.execute(
            text(
                """
                SELECT subject, username, email, name, access_token_hash, session_expires_at
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

    session_expires_at = row["session_expires_at"]
    if isinstance(session_expires_at, datetime) and session_expires_at <= datetime.now(timezone.utc):
        raise _unauthorized("Expired session")

    if row["subject"] != subject:
        raise _unauthorized("Session subject does not match token")

    if row["access_token_hash"] != hash_access_token(token):
        raise _unauthorized("Session token does not match")

    return AuthenticatedUser(
        subject=subject,
        username=row["username"],
        email=row["email"],
        name=row["name"],
        claims=claims,
    )
