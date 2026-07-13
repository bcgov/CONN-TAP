"""ISP spend indicator cards dataset."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.datasets.base import DatasetResult, DatasetService
from app.datasets.chart_format import to_float

from .schema import Filters


class Service(DatasetService):
    id = "isp-spend-indicators"
    name = "ISP Spend Indicators"
    description = "Total spend indicator cards for TSMA & NGTA, TELUS, and Rogers."

    def run(self, db: Session, filters: dict[str, Any]) -> DatasetResult:
        parsed = Filters(**filters)

        def _pg_text_array(values: list[str] | None) -> str | None:
            return "{" + ",".join(values) + "}" if values else None

        df = self.execute_sql(
            db,
            "isp_spend_indicators",
            params={
                "year_type": parsed.year_type.value,
                "period": _pg_text_array(parsed.period),
            },
        )

        if df.empty or df.iloc[0]["total_spend"] is None:
            total = telus = rogers = 0.0
        else:
            row = df.iloc[0]
            total = round(to_float(row["total_spend"]) / 1_000_000, 1)
            telus = round(to_float(row["telus_spend"]) / 1_000_000, 1)
            rogers = round(to_float(row["rogers_spend"]) / 1_000_000, 1)

        indicators = [
            {"label": "Total TSMA & NGTA Spend", "value_millions": total},
            {"label": "Total TELUS Spend", "value_millions": telus},
            {"label": "Total Rogers Spend", "value_millions": rogers},
        ]

        return DatasetResult(
            columns=["label", "value_millions"],
            rows=[[ind["label"], ind["value_millions"]] for ind in indicators],
            row_count=len(indicators),
            metadata={
                "dataset": self.id,
                "filters": parsed.model_dump(mode="json"),
                "chart": {"indicators": indicators},
            },
        )
