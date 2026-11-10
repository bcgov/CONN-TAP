"""Entra app role → Postgres role mapping (DMP-211)."""
from app.core.roles import database_role


def test_each_app_role_maps_to_its_database_role() -> None:
    assert database_role(["global_admin"]) == "tap_global_admin"
    assert database_role(["global_analyst"]) == "tap_global_analyst"
    assert database_role(["org_admin"]) == "tap_org_admin"
    assert database_role(["org_analyst"]) == "tap_org_analyst"


def test_highest_role_wins() -> None:
    assert database_role(["org_analyst", "global_admin"]) == "tap_global_admin"
    assert database_role(["org_admin", "global_analyst"]) == "tap_global_analyst"
    assert database_role(["org_analyst", "org_admin"]) == "tap_org_admin"


def test_no_tap_role_gives_no_database_role() -> None:
    assert database_role([]) is None
    assert database_role(["some_other_app_role"]) is None
