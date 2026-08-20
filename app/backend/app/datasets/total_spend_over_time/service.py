"""Total spend over time dataset — powers the timeline range selector."""
from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.datasets.base import DatasetResult, DatasetService


class Service(DatasetService):
    id = "total-spend-over-time"
    name = "Total Spend Over Time"
    description = "Monthly total spend for all periods — used by the timeline range selector."

    def run(self, db: Session, filters: dict[str, Any]) -> DatasetResult:
        df = self.execute_sql(db, "monthly")

        points = []
        for row in df.itertuples(index=False):
            month = pd.Timestamp(row.period_key)
            points.append({
                "period": month.strftime("%Y-%m"),
                "label": month.strftime("%b %Y"),
                "value": round(float(row.total_spend_millions or 0), 6),
            })

        return DatasetResult(
            columns=["period", "label", "value"],
            rows=[[p["period"], p["label"], p["value"]] for p in points],
            row_count=len(points),
            metadata={"dataset": self.id, "chart": {"data": points, "valueLabel": "Total Spend"}},
        )
