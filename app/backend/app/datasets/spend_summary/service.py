"""Spend summary dataset — powers the BGE / Sub-org / SD summary table."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.datasets.base import DatasetResult, DatasetService
from app.datasets.spend_common import Filters, run_period_query
from .helpers import build_summary_result


class Service(DatasetService):
    id = "spend-summary"
    name = "Spend Summary"
    description = (
        "Telecom spend by BGE / Sub-org / Service Designee, broken out by service "
        "category — used by the summary table."
    )
    required_roles = ("global_admin",)

    def run(self, db: Session, filters: dict[str, Any]) -> DatasetResult:
        parsed = Filters(**filters)
        df = run_period_query(self, db, parsed)
        # Full predefined hierarchy (all BGE / sub_bge / SD), independent of spend,
        # so entities with no data still render as zero rows.
        scaffold_df = self.execute_sql(db, "scaffold")
        return build_summary_result(self.id, df, scaffold_df, parsed)
