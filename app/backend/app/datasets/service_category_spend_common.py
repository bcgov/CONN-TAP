"""Shared formatting for service category spend chart datasets."""
from __future__ import annotations

from enum import StrEnum
from typing import Any

import pandas as pd
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.datasets.base import DatasetResult, DatasetService
from app.datasets.chart_format import fmt_spend, to_float


class YearType(StrEnum):
    calendar = "calendar"
    fiscal = "fiscal"


class Filters(BaseModel):
    year_type: YearType = YearType.fiscal
    year: int | None = None
    quarter: int | None = None


PROVIDER_ORDER = ("TELUS", "Rogers")
PROVIDER_COLOURS = {
    "Rogers": "#e02b24",
    "TELUS": "#b6f396",
}
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
            "year": filters.year,
            "quarter": filters.quarter,
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


def build_plotly_result(dataset_id: str, df: pd.DataFrame, filters: Filters) -> DatasetResult:
    categories = list(dict.fromkeys(df["service_category"].tolist())) if not df.empty else []
    traces = []

    provider_values: dict[str, list[float]] = {}
    for provider in PROVIDER_ORDER:
        provider_key = provider.lower()
        provider_df = df[df["vendor"] == provider_key] if not df.empty else pd.DataFrame()
        values = []
        for category in categories:
            match = provider_df[provider_df["service_category"] == category]
            values.append(
                round(to_float(match["spend_millions"].iloc[0]), 6) if not match.empty else 0
            )
        provider_values[provider] = values

    for provider in PROVIDER_ORDER:
        values = provider_values[provider]
        traces.append(
            {
                "type": "bar",
                "name": provider,
                "x": categories,
                "y": values,
                "text": [f"{provider} - {fmt_spend(v)}" if v else "" for v in values],
                "textposition": "none",
                "textfont": {"size": 10, "color": "#474543"},
                "marker": {"color": PROVIDER_COLOURS[provider]},
                "hovertemplate": "%{x}<br>%{fullData.name}: $%{y:.2f}M<extra></extra>",
            }
        )

    max_stack = (
        max(
            sum(provider_values[p][i] for p in PROVIDER_ORDER)
            for i in range(len(categories))
        )
        if categories else 0
    )

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
                },
            },
        },
    )
