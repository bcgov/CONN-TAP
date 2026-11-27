"""Tests for the reporting status dataset."""
from datetime import date
from pathlib import Path

import pandas as pd

from app.core.roles import ORG_ADMIN, ORG_USER, TO_ADMIN, TO_VIEWER
from app.datasets.reporting_status import service
from app.datasets.reporting_status.service import Service

MODULE_DIR = Path(service.__file__).parent


def received(rows: list[tuple[str, str]]) -> pd.DataFrame:
    """Rows of (report_name, "YYYY-MM") as the query returns them."""
    return pd.DataFrame(
        [{"report_name": name, "period_key": date(int(month[:4]), int(month[5:]), 1)} for name, month in rows],
        columns=["report_name", "period_key"],
    )


def run_with(monkeypatch, df: pd.DataFrame, periods: list[str]):
    def fake_execute_sql(self, db, name, params=None):
        assert name == "received_months"
        return df

    monkeypatch.setattr(Service, "execute_sql", fake_execute_sql)
    return Service(MODULE_DIR).run(db=None, filters={"period": periods})


def every_monthly_report(months: list[str]) -> list[tuple[str, str]]:
    return [(name, month) for month in months for name in ("TELUS", "Rogers Cellular", "Rogers Data")]


def test_every_role_can_use_it() -> None:
    assert set(Service.required_roles) == {TO_ADMIN, TO_VIEWER, ORG_ADMIN, ORG_USER}


def test_nothing_missing_when_every_report_is_in(monkeypatch) -> None:
    months = ["2026-07", "2026-08", "2026-09"]
    df = received(every_monthly_report(months) + [("TSMA", "2026-07"), ("TSMA Lite", "2026-09")])

    result = run_with(monkeypatch, df, months)

    # 3 monthly reports x 3 months, plus TSMA and TSMA Lite once for Jul–Sep.
    assert result.metadata["expected_count"] == 11
    assert result.metadata["received_count"] == 11
    assert result.metadata["missing"] == []


def test_lists_missing_monthly_report(monkeypatch) -> None:
    months = ["2026-07", "2026-08"]
    rows = [row for row in every_monthly_report(months) if row != ("Rogers Data", "2026-08")]

    result = run_with(monkeypatch, received(rows), months)

    assert result.metadata["expected_count"] == 6
    assert result.metadata["received_count"] == 5
    assert result.metadata["missing"] == [
        {"report": "Rogers Data", "provider": "Rogers", "service_type": "Wireline",
         "frequency": "monthly", "period": "Aug 2026"}
    ]
    assert result.rows == [["Rogers Data", "Rogers", "Wireline", "monthly", "Aug 2026"]]


def test_quarterly_report_only_expected_once_the_quarter_ends(monkeypatch) -> None:
    # Oct and Nov are selected but the Oct–Dec quarter hasn't ended, so TSMA isn't
    # expected for it yet. Jul–Sep has no TSMA data, so it's missing.
    months = ["2026-08", "2026-09", "2026-10", "2026-11"]
    df = received(every_monthly_report(months) + [("TSMA", "2026-03"), ("TSMA Lite", "2026-09")])

    result = run_with(monkeypatch, df, months)

    assert result.metadata["missing"] == [
        {"report": "TSMA", "provider": "TELUS", "service_type": "",
         "frequency": "quarterly", "period": "Jul–Sep 2026"}
    ]


def test_report_not_expected_before_its_first_month(monkeypatch) -> None:
    # TELUS starts May 2025 and Rogers Cellular June 2025, so only TELUS is expected
    # in May. Rogers Data starts Feb 2026, so it isn't expected at all here.
    # TSMA and TSMA Lite (from Jan 2025) are expected for Apr–Jun 2025.
    months = ["2025-04", "2025-05", "2025-06"]
    df = received([("TELUS", "2025-05"), ("TELUS", "2025-06"), ("Rogers Cellular", "2025-06"),
                   ("TSMA", "2025-04"), ("TSMA Lite", "2025-04")])

    result = run_with(monkeypatch, df, months)

    assert result.metadata["expected_count"] == 5
    assert result.metadata["missing"] == []


def test_missing_reports_are_listed_in_date_order(monkeypatch) -> None:
    months = ["2026-08", "2026-09"]
    df = received([("Rogers Cellular", "2026-09"), ("Rogers Data", "2026-08"), ("Rogers Data", "2026-09"),
                   ("TSMA", "2026-09"), ("TSMA Lite", "2026-09")])

    result = run_with(monkeypatch, df, months)

    assert [(item["report"], item["period"]) for item in result.metadata["missing"]] == [
        ("Rogers Cellular", "Aug 2026"),
        ("TELUS", "Aug 2026"),
        ("TELUS", "Sep 2026"),
    ]


def test_report_with_no_data_at_all_is_missing_every_time(monkeypatch) -> None:
    months = ["2026-08", "2026-09"]
    df = received(every_monthly_report(months) + [("TSMA", "2026-09")])

    result = run_with(monkeypatch, df, months)

    assert result.metadata["missing"] == [
        {"report": "TSMA Lite", "provider": "TELUS", "service_type": "",
         "frequency": "quarterly", "period": "Jul–Sep 2026"}
    ]


def test_no_months_selected_expects_nothing(monkeypatch) -> None:
    result = run_with(monkeypatch, received([]), [])

    assert result.metadata["expected_count"] == 0
    assert result.metadata["received_count"] == 0
    assert result.metadata["missing"] == []
