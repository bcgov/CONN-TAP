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


def test_fmt_spend_dollars() -> None:
    assert fmt_spend(0.000_015_9) == "$16"


def test_fmt_spend_cents() -> None:
    # Below a dollar the whole-dollar format would read as $0, hiding the figure.
    assert fmt_spend(0.000_000_3) == "$0.30"


def test_fmt_spend_negative() -> None:
    # Net credit, as the Unknown category is: accounting parentheses rather than a
    # minus, which would render as "Rogers - -$2.7K" once the label is assembled.
    assert fmt_spend(-0.002_661_62) == "($2.7K)"


def test_fmt_spend_zero_is_labelled() -> None:
    # A category whose charges and credits cancel still gets a number, so the bar
    # reads as balanced rather than broken.
    assert fmt_spend(0) == "$0"
