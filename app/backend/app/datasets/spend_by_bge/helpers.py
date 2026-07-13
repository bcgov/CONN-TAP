"""Query and chart-building helpers for the spend by BGE dataset."""
from __future__ import annotations

import pandas as pd

from app.datasets.base import DatasetResult
from app.datasets.chart_format import to_float
from app.datasets.spend_common import Filters, PROVIDER_ORDER, run_period_query as run_query

RESULT_COLUMNS = ["organization_name", "vendor", "spend_amount", "spend_millions"]

# Map lowercase DB vendor names → canonical PROVIDER_ORDER casing
_VENDOR_NORM: dict[str, str] = {v.lower(): v for v in PROVIDER_ORDER}

BGE_ORDER = (
    "Gov BC",
    "BCLC",
    "BC Hydro",
    "WSBC",
    "ECC",
    "FHA",
    "NHA",
    "ICBC",
    "PHSA",
    "VIHA",
    "FNHA",
    "VCHA (+PHC)",
    "School Districts",
    "IHA",
)


def build_bar_result(dataset_id: str, df: pd.DataFrame, filters: Filters) -> DatasetResult:
    if df.empty:
        return DatasetResult(
            columns=RESULT_COLUMNS,
            rows=[],
            row_count=0,
            metadata={
                "dataset": dataset_id,
                "filters": filters.model_dump(mode="json"),
                "chart": {"data": [], "vendors": list(PROVIDER_ORDER), "total_millions": 0.0},
            },
        )

    # Pivot keyed by bge_code; also track full name per code
    pivot: dict[str, dict[str, float]] = {}
    code_to_name: dict[str, str] = {}
    for row in df.itertuples(index=False):
        code = str(row.bge_code)
        code_to_name[code] = str(row.organization_name)
        raw_vendor = str(row.vendor)
        vendor = _VENDOR_NORM.get(raw_vendor.lower(), raw_vendor)
        pivot.setdefault(code, {})[vendor] = pivot.get(code, {}).get(vendor, 0.0) + to_float(row.spend_millions)

    grand_total = sum(v for org_data in pivot.values() for v in org_data.values())
    vendors = list(PROVIDER_ORDER)

    chart_data = []
    for code in BGE_ORDER:
        if code not in pivot:
            continue
        entry: dict = {"bge_code": code, "organization_name": code_to_name.get(code, code)}
        for vendor in vendors:
            entry[vendor] = round(pivot[code].get(vendor, 0.0), 6)
        chart_data.append(entry)
    for code, org_data in pivot.items():
        if code not in BGE_ORDER:
            entry = {"bge_code": code, "organization_name": code_to_name.get(code, code)}
            for vendor in vendors:
                entry[vendor] = round(org_data.get(vendor, 0.0), 6)
            chart_data.append(entry)

    tabular_rows = [
        [str(row.organization_name), str(row.vendor), round(to_float(row.spend_amount), 2), round(to_float(row.spend_millions), 6)]
        for row in df.itertuples(index=False)
    ]

    return DatasetResult(
        columns=RESULT_COLUMNS,
        rows=tabular_rows,
        row_count=len(tabular_rows),
        metadata={
            "dataset": dataset_id,
            "filters": filters.model_dump(mode="json"),
            "chart": {
                "data": chart_data,
                "vendors": vendors,
                "total_millions": round(grand_total, 6),
            },
        },
    )
