"""Shared formatting for service category spend chart datasets."""
from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.datasets.base import DatasetResult, DatasetService


class YearType(StrEnum):
    calendar = "calendar"
    fiscal = "fiscal"


class Filters(BaseModel):
    year_type: YearType = YearType.fiscal
    year: int | None = Field(default=None, ge=1900, le=2100)
    quarter: int | None = Field(default=None, ge=1, le=4)

    @field_validator("year", "quarter", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: Any) -> Any:
        if value == "":
            return None
        return value


VENDOR_ORDER = ("Rogers", "Telus")
VENDOR_COLOURS = {
    "Rogers": "#da291c",
    "Telus": "#4b286d",
}
RESULT_COLUMNS = [
    "service_category",
    "vendor",
    "spend_amount",
    "spend_millions",
    "total_spend_millions",
]


def _to_float(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)
    if value is None:
        return 0.0
    return float(value)


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

    df["spend_amount"] = df["spend_amount"].map(_to_float)
    df["spend_millions"] = df["spend_millions"].map(_to_float)
    df["total_spend_millions"] = df["total_spend_millions"].map(_to_float)
    return df


def to_tabular_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {
            "service_category": str(row.service_category),
            "vendor": str(row.vendor).title(),
            "spend_amount": round(_to_float(row.spend_amount), 2),
            "spend_millions": round(_to_float(row.spend_millions), 6),
            "total_spend_millions": round(_to_float(row.total_spend_millions), 6),
        }
        for row in df.itertuples(index=False)
    ]


def build_plotly_result(dataset_id: str, df: pd.DataFrame, filters: Filters) -> DatasetResult:
    categories = list(dict.fromkeys(df["service_category"].tolist())) if not df.empty else []
    traces = []

    for vendor in VENDOR_ORDER:
        vendor_key = vendor.lower()
        vendor_df = df[df["vendor"] == vendor_key] if not df.empty else pd.DataFrame()
        values = []
        for category in categories:
            match = vendor_df[vendor_df["service_category"] == category]
            values.append(
                round(_to_float(match["spend_millions"].iloc[0]), 6) if not match.empty else 0
            )

        traces.append(
            {
                "type": "bar",
                "name": vendor,
                "x": categories,
                "y": values,
                "marker": {"color": VENDOR_COLOURS[vendor]},
                "hovertemplate": "%{x}<br>%{fullData.name}: $%{y:.2f}M<extra></extra>",
            }
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
                        "title": "Service category",
                        "categoryorder": "array",
                        "categoryarray": categories,
                    },
                    "yaxis": {"title": "Spend ($M)", "rangemode": "tozero"},
                    "margin": {"l": 72, "r": 24, "t": 24, "b": 96},
                    "legend": {"orientation": "h", "x": 0, "y": 1.12},
                },
            },
        },
    )


def build_recharts_result(dataset_id: str, df: pd.DataFrame, filters: Filters) -> DatasetResult:
    rows_by_category: dict[str, dict[str, Any]] = {}

    for row in df.itertuples(index=False):
        category = str(row.service_category)
        vendor = str(row.vendor).title()
        category_row = rows_by_category.setdefault(
            category,
            {"serviceCategory": category, "Rogers": 0.0, "Telus": 0.0, "total": 0.0},
        )
        category_row[vendor] = round(_to_float(row.spend_millions), 6)
        category_row["total"] = round(_to_float(row.total_spend_millions), 6)

    chart_rows = sorted(rows_by_category.values(), key=lambda item: item["total"], reverse=True)
    rows = to_tabular_rows(df)

    return DatasetResult(
        columns=RESULT_COLUMNS,
        rows=[[row[column] for column in RESULT_COLUMNS] for row in rows],
        row_count=len(rows),
        metadata={
            "dataset": dataset_id,
            "library": "recharts",
            "filters": filters.model_dump(mode="json"),
            "chart": {
                "data": chart_rows,
                "bars": [
                    {"dataKey": vendor, "stackId": "spend", "fill": VENDOR_COLOURS[vendor], "name": vendor}
                    for vendor in VENDOR_ORDER
                ],
                "xAxisKey": "serviceCategory",
                "yAxisLabel": "Spend ($M)",
            },
        },
    )
