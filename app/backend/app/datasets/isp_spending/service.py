"""ISP Spending dataset service."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.datasets.base import DatasetResult, DatasetService

from .schema import Filters


class Service(DatasetService):
    id = "isp-spending"
    name = "ISP Spending"
    description = "Aggregated ISP spending by region and year."

    def run(self, db: Session, filters: dict[str, Any]) -> DatasetResult:
        parsed = Filters(**filters)
        query_name = filters.get("query") or self.config.get("default_query", "by_region_year")

        df = self.execute_sql(
            db,
            query_name,
            params={
                "region": parsed.region,
                "year": parsed.year,
                "limit": parsed.limit,
            },
        )

        return DatasetResult.from_dataframe(
            df,
            metadata={
                "dataset": self.id,
                "query": query_name,
                "filters": parsed.model_dump(),
            },
        )
