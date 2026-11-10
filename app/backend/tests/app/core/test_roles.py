"""Entra app role → Postgres role mapping (DMP-211)."""
from app.core.roles import database_role


def test_each_app_role_maps_to_its_database_role() -> None:
    assert database_role(["to_admin"]) == "tap_to_admin"
    assert database_role(["to_viewer"]) == "tap_to_viewer"
    assert database_role(["org_admin"]) == "tap_org_admin"
    assert database_role(["org_user"]) == "tap_org_user"


def test_highest_role_wins() -> None:
    assert database_role(["org_user", "to_admin"]) == "tap_to_admin"
    assert database_role(["org_admin", "to_viewer"]) == "tap_to_viewer"
    assert database_role(["org_user", "org_admin"]) == "tap_org_admin"


def test_no_tap_role_gives_no_database_role() -> None:
    assert database_role([]) is None
    assert database_role(["some_other_app_role"]) is None
    assert database_role(["org_analyst"]) is None  # old name, no longer a TAP role
