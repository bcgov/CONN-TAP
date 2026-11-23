"""Tests for the ISP spend indicator cards dataset."""
from pathlib import Path

import pandas as pd

from app.core.roles import ORG_ADMIN, ORG_USER, TO_ADMIN, TO_VIEWER
from app.datasets.isp_spend_indicators import service
from app.datasets.isp_spend_indicators.service import Service

MODULE_DIR = Path(service.__file__).parent


def run_with(monkeypatch, df: pd.DataFrame, filters: dict | None = None):
    calls = []

    def fake_execute_sql(self, db, name, params=None):
        calls.append((name, params))
        return df

    monkeypatch.setattr(Service, "execute_sql", fake_execute_sql)
    return Service(MODULE_DIR).run(db=None, filters=filters or {}), calls


def test_every_role_can_use_it() -> None:
    # Org users only get their own organizations' rows (row-level security).
    assert set(Service.required_roles) == {TO_ADMIN, TO_VIEWER, ORG_ADMIN, ORG_USER}


def test_returns_total_and_provider_spend_in_millions(monkeypatch) -> None:
    df = pd.DataFrame(
        [{"total_spend": 7_984_321.5, "telus_spend": 5_000_000.0, "rogers_spend": 2_984_321.5}]
    )

    result, calls = run_with(monkeypatch, df, {"period": ["2026-01", "2026-02"]})

    assert calls[0][0] == "isp_spend_indicators"
    assert result.metadata["chart"]["indicators"] == [
        {"label": "Total TSMA & NGTA Spend", "value_millions": 7.984322},
        {"label": "Total TELUS Spend", "value_millions": 5.0, "provider": "TELUS"},
        {"label": "Total Rogers Spend", "value_millions": 2.984322, "provider": "Rogers"},
    ]
    assert result.rows == [
        ["Total TSMA & NGTA Spend", 7.984322],
        ["Total TELUS Spend", 5.0],
        ["Total Rogers Spend", 2.984322],
    ]


def test_returns_zeros_when_there_is_no_spend(monkeypatch) -> None:
    # An org user with no rows gets a single row of NULL sums.
    df = pd.DataFrame([{"total_spend": None, "telus_spend": None, "rogers_spend": None}])

    result, _ = run_with(monkeypatch, df)

    values = [item["value_millions"] for item in result.metadata["chart"]["indicators"]]
    assert values == [0.0, 0.0, 0.0]
