"""Query and chart-building helpers for the service category spend dataset."""
from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.datasets.base import DatasetResult, DatasetService
from app.datasets.chart_format import fmt_spend, to_float
from app.datasets.colors import PROVIDER_COLOURS, TEXT_SECONDARY
from app.datasets.spend_common import Filters, pg_text_array, PROVIDER_ORDER
RESULT_COLUMNS = [
    "service_category",
    "vendor",
    "spend_amount",
    "spend_millions",
    "total_spend_millions",
]


def run_query(service: DatasetService, db: Session, filters: Filters) -> pd.DataFrame:
    df = service.execute_sql(
        db,
        "service_category_vendor_spend",
        params={
            "year_type": filters.year_type.value,
            "period": pg_text_array(filters.period),
        },
    )

    if df.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    df["spend_amount"] = df["spend_amount"].map(to_float)
    df["spend_millions"] = df["spend_millions"].map(to_float)
    df["total_spend_millions"] = df["total_spend_millions"].map(to_float)
    return df


def to_tabular_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {
            "service_category": str(row.service_category),
            "vendor": str(row.vendor).title(),
            "spend_amount": round(to_float(row.spend_amount), 2),
            "spend_millions": round(to_float(row.spend_millions), 6),
            "total_spend_millions": round(to_float(row.total_spend_millions), 6),
        }
        for row in df.itertuples(index=False)
    ]


def _flat_annotations(
    categories: list[str], provider_labels: dict[str, list[str]], flat: set[int]
) -> list[dict[str, Any]]:
    """Label the categories that have no bar to hang their text on.

    Annotations are positioned against the axes rather than a bar, so the figure
    shows whether or not a rect exists. Providers are stacked top-down, matching
    how the frontend combines the bar labels.
    """
    annotations = []
    for i in sorted(flat):
        text = "<br>".join(
            label
            for provider in reversed(PROVIDER_ORDER)
            if (label := provider_labels[provider][i])
        )
        if not text:
            continue
        annotations.append(
            {
                "x": categories[i],
                "y": 0,
                "text": text,
                "showarrow": False,
                "yanchor": "bottom",
                "yshift": 6,
                "font": {"size": 10, "color": TEXT_SECONDARY},
            }
        )
    return annotations


def build_plotly_result(dataset_id: str, df: pd.DataFrame, filters: Filters) -> DatasetResult:
    categories = list(dict.fromkeys(df["service_category"].tolist())) if not df.empty else []
    traces = []

    provider_values: dict[str, list[float]] = {}
    provider_amounts: dict[str, list[float | None]] = {}
    for provider in PROVIDER_ORDER:
        provider_key = provider.lower()
        provider_df = df[df["vendor"] == provider_key] if not df.empty else pd.DataFrame()
        values: list[float] = []
        amounts: list[float | None] = []
        for category in categories:
            match = provider_df[provider_df["service_category"] == category]
            if match.empty:
                values.append(0)
                amounts.append(None)
                continue
            values.append(round(to_float(match["spend_millions"].iloc[0]), 6))
            amounts.append(to_float(match["spend_amount"].iloc[0]))
        provider_values[provider] = values
        provider_amounts[provider] = amounts

    provider_labels = {
        provider: [
            f"{provider} - {fmt_spend(a / 1_000_000)}" if a is not None else ""
            for a in provider_amounts[provider]
        ]
        for provider in PROVIDER_ORDER
    }
    stacks = [sum(provider_values[p][i] for p in PROVIDER_ORDER) for i in range(len(categories))]
    flat = {i for i, total in enumerate(stacks) if total <= 0}

    for provider in PROVIDER_ORDER:
        traces.append(
            {
                "type": "bar",
                "name": provider,
                "x": categories,
                "y": provider_values[provider],
                "text": [
                    "" if i in flat else label
                    for i, label in enumerate(provider_labels[provider])
                ],
                "textposition": "none",
                "textfont": {"size": 10, "color": TEXT_SECONDARY},
                "marker": {"color": PROVIDER_COLOURS[provider]},
                "hovertemplate": "%{x}<br>%{fullData.name}: $%{y:.2f}M<extra></extra>",
            }
        )

    annotations = _flat_annotations(categories, provider_labels, flat)
    max_stack = max(stacks) if stacks else 0

    rows = to_tabular_rows(df)
    return DatasetResult(
        columns=RESULT_COLUMNS,
        rows=[[row[column] for column in RESULT_COLUMNS] for row in rows],
        row_count=len(rows),
        metadata={
            "dataset": dataset_id,
            "library": "plotly",
            "filters": filters.model_dump(mode="json"),
            "chart": {
                "data": traces,
                "layout": {
                    "barmode": "stack",
                    "xaxis": {
                        "title": {"text": "Service category", "font": {"size": 11}},
                        "categoryorder": "array",
                        "categoryarray": categories,
                    },
                    "yaxis": {"title": {"text": "Spend ($M)", "font": {"size": 11}}, "range": [0, max_stack * 1.25]},
                    "margin": {"l": 72, "r": 24, "t": 24, "b": 96},
                    "legend": {"orientation": "h", "x": 0, "y": 1.12, "font": {"size": 11}},
                    "annotations": annotations,
                },
            },
        },
    )
