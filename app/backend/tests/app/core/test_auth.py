"""Role-based access logic added to ``AuthenticatedUser`` (DMP-205)."""
from app.core.auth import AuthenticatedUser


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
