"""Service category spend dataset formatted for Plotly."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.datasets.base import DatasetResult, DatasetService
from app.datasets.service_category_spend_common import Filters, build_plotly_result, run_query


class Service(DatasetService):
    id = "service-category-spend-plotly"
    name = "Service Category Spend - Plotly"
    description = "Stacked spend by service category and provider formatted for Plotly."

    def run(self, db: Session, filters: dict[str, Any]) -> DatasetResult:
        parsed = Filters(**filters)
        df = run_query(self, db, parsed)
        return build_plotly_result(self.id, df, parsed)
