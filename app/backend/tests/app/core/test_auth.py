"""Role-based access logic added to ``AuthenticatedUser`` (DMP-205)."""
import pytest
from fastapi import HTTPException

from app.core.auth import AuthenticatedUser, get_current_user


class _FakeDb:
    """Returns ``session_row`` for the session lookup and records every statement."""

    def __init__(self, session_row: dict) -> None:
        self.session_row = session_row
        self.statements: list[tuple[str, dict | None]] = []

    def execute(self, statement: str, params: dict | None = None) -> "_FakeDb":
        self.statements.append((statement, params))
        return self

    def mappings(self) -> "_FakeDb":
        return self

    def first(self) -> dict:
        return self.session_row


def _session_row(roles: list[str]) -> dict:
    return {
        "subject": "oid-1",
        "username": "alice",
        "email": None,
        "name": None,
        "claims": {"roles": roles},
    }


def _user(roles: list[str]) -> AuthenticatedUser:
    return AuthenticatedUser(
        subject="sub-1",
        username="alice",
        email="alice@example.com",
        name="Alice",
        claims={},
        roles=roles,
    )


def test_open_dataset_allows_user_without_roles() -> None:
    assert _user([]).has_any_role(()) is True


def test_open_dataset_allows_user_with_roles() -> None:
    assert _user(["viewer"]).has_any_role(()) is True


def test_matching_role_grants_access() -> None:
    assert _user(["admin", "viewer"]).has_any_role(("admin",)) is True


def test_any_of_several_required_roles_grants_access() -> None:
    assert _user(["editor"]).has_any_role(("admin", "editor")) is True


def test_non_matching_role_denies_access() -> None:
    assert _user(["viewer"]).has_any_role(("admin",)) is False


def test_user_without_roles_denied_when_role_required() -> None:
    assert _user([]).has_any_role(("admin",)) is False


# ---- get_current_user switches to the user's database role (DMP-211) --------


def test_request_runs_as_the_users_database_role() -> None:
    db = _FakeDb(_session_row(["global_analyst"]))

    user = get_current_user(session_cookie="cookie", db=db)

    assert user.roles == ["global_analyst"]
    statement, params = db.statements[-1]
    assert "set_config('role'" in statement
    assert params == {"role": "tap_global_analyst"}


def test_user_without_tap_role_is_refused_before_switching_role() -> None:
    db = _FakeDb(_session_row(["some_other_app_role"]))

    with pytest.raises(HTTPException) as exc:
        get_current_user(session_cookie="cookie", db=db)

    assert exc.value.status_code == 403
    assert len(db.statements) == 1  # only the session lookup
