"""Service category spend dataset formatted for Recharts."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.datasets.base import DatasetResult, DatasetService
from app.datasets.service_category_spend_common import Filters, build_recharts_result, run_query


class Service(DatasetService):
    id = "service-category-spend-recharts"
    name = "Service Category Spend - Recharts"
    description = "Stacked spend by service category and vendor formatted for Recharts."

    def run(self, db: Session, filters: dict[str, Any]) -> DatasetResult:
        parsed = Filters(**filters)
        df = run_query(self, db, parsed)
        return build_recharts_result(self.id, df, parsed)
