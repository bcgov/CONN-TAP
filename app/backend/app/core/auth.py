"""FastAPI dependencies for shared Next.js/Keycloak sessions."""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
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

logger = logging.getLogger("app.auth")

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
        logger.warning(
            "auth reject: missing credentials (cookie=%s, bearer=%s)",
            bool(session_cookie),
            credentials is not None,
        )
        raise _unauthorized()

    token = credentials.credentials
    claims = _validate_token(token)
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise _unauthorized("Token is missing subject")

    session_hash = hash_session_token(session_cookie)
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
            {"session_hash": session_hash},
        )
        .mappings()
        .first()
    )

    # Short, non-secret fingerprints to correlate a single browser's requests
    # across log lines without exposing the cookie or token themselves.
    session_fp = session_hash[:8]
    subject_fp = subject[:12]

    if row is None:
        # Either the session was never written, or it has been revoked/expired.
        existing = (
            db.execute(
                text(
                    "SELECT revoked_at, session_expires_at FROM auth_sessions WHERE session_hash = :h"
                ),
                {"h": session_hash},
            )
            .mappings()
            .first()
        )
        if existing is None:
            reason = "no row for session_hash"
        elif existing["revoked_at"] is not None:
            reason = f"row revoked at {existing['revoked_at'].isoformat()}"
        else:
            reason = f"row session_expires_at={existing['session_expires_at'].isoformat()} (now past)"
        logger.warning(
            "auth reject: Invalid session sub=%s session_fp=%s reason=%s", subject_fp, session_fp, reason
        )
        raise _unauthorized("Invalid session")

    session_expires_at = row["session_expires_at"]
    if isinstance(session_expires_at, datetime) and session_expires_at <= datetime.now(timezone.utc):
        logger.warning("auth reject: Expired session sub=%s session_fp=%s", subject_fp, session_fp)
        raise _unauthorized("Expired session")

    if row["subject"] != subject:
        logger.warning(
            "auth reject: subject mismatch token_sub=%s row_sub=%s session_fp=%s",
            subject_fp,
            str(row["subject"])[:12],
            session_fp,
        )
        raise _unauthorized("Session subject does not match token")

    if row["access_token_hash"] != hash_access_token(token):
        # Most often means the proxy sent a bearer that no longer matches the
        # stored (rotated) access token, i.e. a refresh-token race.
        logger.warning(
            "auth reject: access-token hash mismatch sub=%s session_fp=%s", subject_fp, session_fp
        )
        raise _unauthorized("Session token does not match")

    return AuthenticatedUser(
        subject=subject,
        username=row["username"],
        email=row["email"],
        name=row["name"],
        claims=claims,
    )
