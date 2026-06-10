from decimal import Decimal

from app.datasets.chart_format import fmt_spend, to_float


def test_to_float_from_decimal() -> None:
    assert to_float(Decimal("1.5")) == 1.5


def test_to_float_from_none() -> None:
    assert to_float(None) == 0.0


def test_fmt_spend_millions() -> None:
    assert fmt_spend(2.5) == "$2.5M"


def test_fmt_spend_thousands() -> None:
    assert fmt_spend(0.5) == "$500.0K"


def test_fmt_spend_zero() -> None:
    assert fmt_spend(0) == ""
