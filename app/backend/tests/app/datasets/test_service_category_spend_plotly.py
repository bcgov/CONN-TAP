"""Tests for the service-category spend chart builder."""
import pandas as pd

from app.datasets.service_category_spend_plotly.helpers import build_plotly_result
from app.datasets.spend_common import Filters

FILTERS = Filters(year_type="fiscal", period=["2026_2"])

COLUMNS = [
    "service_category",
    "vendor",
    "spend_amount",
    "spend_millions",
    "total_spend_millions",
]


def row(category, vendor, amount):
    return {
        "service_category": category,
        "vendor": vendor,
        "spend_amount": amount,
        "spend_millions": amount / 1_000_000,
        "total_spend_millions": amount / 1_000_000,
    }


def chart_of(*records):
    return build_plotly_result("x", pd.DataFrame(list(records)), FILTERS).metadata["chart"]


def test_net_credit_category_is_labelled_by_annotation() -> None:
    # Unknown nets negative: Rogers credits outweigh the late fees. The bar hangs
    # below the axis, which starts at zero, so Plotly has nowhere to draw the
    # text -- the figure comes from a layout annotation pinned to the floor.
    chart = chart_of(
        row("Cellular", "telus", 21_600_000.0),
        row("Unknown", "rogers", -2661.62),
    )

    assert chart["layout"]["annotations"] == [
        {
            "x": "Unknown",
            "y": 0,
            "text": "Rogers - ($2.7K)",
            "showarrow": False,
            "yanchor": "bottom",
            "yshift": 6,
            "font": {"size": 10, "color": "#474543"},
        }
    ]


def test_annotated_category_drops_its_bar_text() -> None:
    # Otherwise a zero-height bar can still draw text across the axis, colliding
    # with the annotation.
    chart = chart_of(
        row("Cellular", "telus", 21_600_000.0),
        row("Unknown", "rogers", -2661.62),
    )

    assert [trace["text"][1] for trace in chart["data"]] == ["", ""]


def test_category_with_spend_keeps_its_bar_text_and_is_not_annotated() -> None:
    chart = chart_of(
        row("Cellular", "telus", 21_600_000.0),
        row("Cellular", "rogers", 6_000_000.0),
    )

    labels = {trace["name"]: trace["text"][0] for trace in chart["data"]}
    assert labels == {"TELUS": "TELUS - $21.6M", "Rogers": "Rogers - $6.0M"}
    assert chart["layout"]["annotations"] == []


def test_provider_absent_from_a_category_is_left_unlabelled() -> None:
    # Distinct from a provider that nets zero, which does get a "$0" figure.
    chart = chart_of(row("Time Limited Services", "telus", 3_900_000.0))

    labels = {trace["name"]: trace["text"][0] for trace in chart["data"]}
    assert labels == {"TELUS": "TELUS - $3.9M", "Rogers": ""}


def test_empty_frame_produces_no_annotations() -> None:
    chart = build_plotly_result(
        "x", pd.DataFrame(columns=COLUMNS), FILTERS
    ).metadata["chart"]

    assert chart["layout"]["annotations"] == []
