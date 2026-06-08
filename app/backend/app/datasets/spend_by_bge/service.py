"""Spend by BGE dataset — powers the BGE bar chart on the landing page."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.datasets.base import DatasetResult, DatasetService
from .helpers import build_bar_result, run_query
from .schema import Filters


class Service(DatasetService):
    id = "spend-by-bge"
    name = "Spend by BGE"
    description = "Total telecom spend aggregated by business government entity — used by the BGE bar chart."

    def run(self, db: Session, filters: dict[str, Any]) -> DatasetResult:
        parsed = Filters(**filters)
        df = run_query(self, db, parsed)
        return build_bar_result(self.id, df, parsed)
