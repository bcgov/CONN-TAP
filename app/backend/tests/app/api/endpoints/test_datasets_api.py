"""Registry-driven dataset endpoints now gate access by client role (DMP-205)."""
from pathlib import Path

import pytest

from app.api.endpoints import datasets_api
from app.api.errors import ApiError
from app.core.auth import AuthenticatedUser
from app.datasets.base import DatasetResult, DatasetService


def _make_service(dataset_id: str, required_roles: tuple[str, ...], tmp_path: Path) -> DatasetService:
    """Build a concrete ``DatasetService`` without touching real config/query files."""
    cls = type(
        "StubService",
        (DatasetService,),
        {
            "id": dataset_id,
            "name": dataset_id,
            "required_roles": required_roles,
            "run": lambda self, db, filters: DatasetResult(
                columns=[], rows=[], row_count=0, metadata={}
            ),
        },
    )
    return cls(module_dir=tmp_path)


def _user(roles: list[str]) -> AuthenticatedUser:
    return AuthenticatedUser(
        subject="sub-1",
        username="alice",
        email=None,
        name=None,
        claims={},
        roles=roles,
    )


# ---- ApiError ---------------------------------------------------------------


def test_api_error_carries_status_and_detail() -> None:
    err = ApiError(403, "nope")
    assert err.status_code == 403
    assert err.detail == "nope"
    assert str(err) == "nope"


# ---- describe() advertises required roles -----------------------------------


def test_describe_reports_required_roles(tmp_path: Path) -> None:
    service = _make_service("spend", ("admin",), tmp_path)
    assert service.describe()["requiredRoles"] == ["admin"]


def test_describe_defaults_to_no_required_roles(tmp_path: Path) -> None:
    service = _make_service("spend", (), tmp_path)
    assert service.describe()["requiredRoles"] == []


# ---- _require_access gate ---------------------------------------------------


def test_require_access_allows_open_dataset(tmp_path: Path) -> None:
    service = _make_service("spend", (), tmp_path)
    datasets_api._require_access(service, _user([]))  # no raise


def test_require_access_allows_authorized_role(tmp_path: Path) -> None:
    service = _make_service("spend", ("admin",), tmp_path)
    datasets_api._require_access(service, _user(["admin"]))  # no raise


def test_require_access_forbids_missing_role(tmp_path: Path) -> None:
    service = _make_service("spend", ("admin",), tmp_path)
    with pytest.raises(ApiError) as exc_info:
        datasets_api._require_access(service, _user(["viewer"]))
    assert exc_info.value.status_code == 403
    assert "spend" in exc_info.value.detail


# ---- list_datasets filters to what the caller may see -----------------------


def test_list_datasets_hides_datasets_the_user_cannot_access(tmp_path: Path, monkeypatch) -> None:
    public = _make_service("public", (), tmp_path)
    restricted = _make_service("restricted", ("admin",), tmp_path)
    monkeypatch.setattr(datasets_api.registry, "all_datasets", lambda: [public, restricted])

    result = datasets_api.list_datasets(user=_user(["viewer"]))

    assert [d["id"] for d in result] == ["public"]


def test_list_datasets_includes_datasets_the_user_can_access(tmp_path: Path, monkeypatch) -> None:
    public = _make_service("public", (), tmp_path)
    restricted = _make_service("restricted", ("admin",), tmp_path)
    monkeypatch.setattr(datasets_api.registry, "all_datasets", lambda: [public, restricted])

    result = datasets_api.list_datasets(user=_user(["admin"]))

    assert {d["id"] for d in result} == {"public", "restricted"}


# ---- describe_dataset endpoint ----------------------------------------------


def test_describe_dataset_unknown_raises_404(monkeypatch) -> None:
    monkeypatch.setattr(datasets_api.registry, "get", lambda _id: None)
    with pytest.raises(ApiError) as exc_info:
        datasets_api.describe_dataset("ghost", user=_user(["admin"]))
    assert exc_info.value.status_code == 404


def test_describe_dataset_forbidden_raises_403(tmp_path: Path, monkeypatch) -> None:
    restricted = _make_service("restricted", ("admin",), tmp_path)
    monkeypatch.setattr(datasets_api.registry, "get", lambda _id: restricted)
    with pytest.raises(ApiError) as exc_info:
        datasets_api.describe_dataset("restricted", user=_user(["viewer"]))
    assert exc_info.value.status_code == 403


def test_describe_dataset_authorized_returns_metadata(tmp_path: Path, monkeypatch) -> None:
    restricted = _make_service("restricted", ("admin",), tmp_path)
    monkeypatch.setattr(datasets_api.registry, "get", lambda _id: restricted)
    result = datasets_api.describe_dataset("restricted", user=_user(["admin"]))
    assert result["id"] == "restricted"
    assert result["requiredRoles"] == ["admin"]
