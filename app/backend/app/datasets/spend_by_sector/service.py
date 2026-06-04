"""Spend by sector dataset — powers the sector pie chart on the landing page."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.datasets.base import DatasetResult, DatasetService
from app.datasets.chart_format import to_float
from app.datasets.service_category_spend_common import Filters

SECTOR_COLOURS = {
    "Health Authorities": "#4e79a7",
    "Crown Corporations": "#c03b27",
    "Gov & ECC": "#76b041",
    "School Districts": "#7b5ea7",
}
SECTOR_ORDER = ("Health Authorities", "Crown Corporations", "Gov & ECC", "School Districts")

RESULT_COLUMNS = ["sector", "vendor", "spend_amount", "spend_millions"]


class Service(DatasetService):
    id = "spend-by-sector"
    name = "Spend by Sector"
    description = "Total telecom spend aggregated by sector — used by the sector pie chart."

    def run(self, db: Session, filters: dict[str, Any]) -> DatasetResult:
        parsed = Filters(**filters)

        def _pg_array(values: list[int] | None) -> str | None:
            return "{" + ",".join(str(v) for v in values) + "}" if values else None

        query_name = "calendar" if parsed.year_type == "calendar" else "fiscal"
        df = self.execute_sql(
            db,
            query_name,
            params={
                "years": _pg_array(parsed.years),
                "quarters": _pg_array(parsed.quarters),
            },
        )

        if df.empty:
            return DatasetResult(
                columns=RESULT_COLUMNS,
                rows=[],
                row_count=0,
                metadata={
                    "dataset": self.id,
                    "filters": parsed.model_dump(mode="json"),
                    "chart": {"data": [], "total_millions": 0.0},
                },
            )

        sector_totals: dict[str, float] = {}
        for row in df.itertuples(index=False):
            sector = str(row.sector)
            sector_totals[sector] = sector_totals.get(sector, 0.0) + to_float(row.spend_millions)

        grand_total = sum(sector_totals.values())

        pie_data = []
        for sector in SECTOR_ORDER:
            if sector not in sector_totals:
                continue
            spend = round(sector_totals[sector], 6)
            pie_data.append({
                "sector": sector,
                "spend_millions": spend,
                "percentage": round(spend / grand_total * 100, 1) if grand_total else 0.0,
                "fill": SECTOR_COLOURS.get(sector, "#888888"),
            })
        for sector, spend in sector_totals.items():
            if sector not in SECTOR_ORDER:
                pie_data.append({
                    "sector": sector,
                    "spend_millions": round(spend, 6),
                    "percentage": round(spend / grand_total * 100, 1) if grand_total else 0.0,
                    "fill": "#aaaaaa",
                })

        tabular_rows = [
            [str(row.sector), str(row.vendor), round(to_float(row.spend_amount), 2), round(to_float(row.spend_millions), 6)]
            for row in df.itertuples(index=False)
        ]

        return DatasetResult(
            columns=RESULT_COLUMNS,
            rows=tabular_rows,
            row_count=len(tabular_rows),
            metadata={
                "dataset": self.id,
                "filters": parsed.model_dump(mode="json"),
                "chart": {
                    "data": pie_data,
                    "total_millions": round(grand_total, 6),
                    "dataKey": "spend_millions",
                    "nameKey": "sector",
                },
            },
        )
