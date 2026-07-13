"""Total spend over time dataset — powers the timeline range selector."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.datasets.base import DatasetResult, DatasetService


class Service(DatasetService):
    id = "total-spend-over-time"
    name = "Total Spend Over Time"
    description = "Quarterly total spend for all periods — used by the timeline range selector."

    def run(self, db: Session, filters: dict[str, Any]) -> DatasetResult:
        year_type = filters.get("year_type", "fiscal")
        query_name = "calendar" if year_type == "calendar" else "fiscal"
        df = self.execute_sql(db, query_name)

        if df.empty:
            return DatasetResult(
                columns=["period", "label", "value"],
                rows=[],
                row_count=0,
                metadata={"dataset": self.id, "chart": {"data": [], "valueLabel": "Total Spend"}},
            )

        points = []
        for row in df.itertuples(index=False):
            year = int(row.year)
            quarter = int(row.quarter)
            label = f"Q{quarter} FY{year}" if query_name == "fiscal" else f"Q{quarter} {year}"
            points.append({
                "period": f"{year}_{quarter}",
                "label": label,
                "value": round(float(row.total_spend_millions or 0), 6),
            })

        return DatasetResult(
            columns=["period", "label", "value"],
            rows=[[p["period"], p["label"], p["value"]] for p in points],
            row_count=len(points),
            metadata={"dataset": self.id, "chart": {"data": points, "valueLabel": "Total Spend"}},
        )
