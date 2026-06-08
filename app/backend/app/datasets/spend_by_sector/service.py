"""Spend by sector dataset — powers the sector pie chart on the landing page."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.datasets.base import DatasetResult, DatasetService
from .helpers import build_pie_result, run_query
from .schema import Filters


class Service(DatasetService):
    id = "spend-by-sector"
    name = "Spend by Sector"
    description = "Total telecom spend aggregated by sector — used by the sector pie chart."

    def run(self, db: Session, filters: dict[str, Any]) -> DatasetResult:
        parsed = Filters(**filters)
        df = run_query(self, db, parsed)
        return build_pie_result(self.id, df, parsed)
