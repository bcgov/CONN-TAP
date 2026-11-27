"""Reporting status dataset: which vendor reports are still missing for the selected months."""
from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.core.roles import ORG_ADMIN, ORG_USER, TO_ADMIN, TO_VIEWER
from app.datasets.base import DatasetResult, DatasetService
from app.datasets.spend_common import Filters

# The reports we expect, in the order they're listed. Names match report_name in
# analytics.report_period_received. Monthly reports are expected every month.
# Quarterly reports are expected once a quarter has ended, i.e. in March, June,
# September and December. first_month is the first month we received the report;
# it isn't expected before that.
EXPECTED_REPORTS = [
    {"name": "Rogers Cellular", "provider": "Rogers", "service_type": "Wireless",
     "frequency": "monthly", "first_month": "2025-06"},
    {"name": "Rogers Data", "provider": "Rogers", "service_type": "Wireline",
     "frequency": "monthly", "first_month": "2026-02"},
    {"name": "TELUS", "provider": "TELUS", "service_type": "Wireless and Wireline",
     "frequency": "monthly", "first_month": "2025-05"},
    {"name": "TSMA", "provider": "TELUS", "service_type": "",
     "frequency": "quarterly", "first_month": "2025-01"},
    {"name": "TSMA Lite", "provider": "TELUS", "service_type": "",
     "frequency": "quarterly", "first_month": "2025-01"},
]

class Service(DatasetService):
    id = "reporting-status"
    name = "Reporting Status"
    description = "Vendor reports expected for the selected months, and which ones haven't come in."
    required_roles = (TO_ADMIN, TO_VIEWER, ORG_ADMIN, ORG_USER)

    def run(self, db: Session, filters: dict[str, Any]) -> DatasetResult:
        parsed = Filters(**filters)
        selected_months = [pd.Period(month, freq="M") for month in sorted(parsed.period or [])]

        df = self.execute_sql(db, "received_months")
        received_months = {
            (row.report_name, pd.Period(row.period_key, freq="M")) for row in df.itertuples(index=False)
        }
        # A quarterly report is received when any month of the quarter has data.
        received_quarters = {(name, month.asfreq("Q")) for name, month in received_months}
        received = received_months | received_quarters

        expected_count = 0
        missing = []

        # Months on the outside, so the missing reports come out in date order.
        for month in selected_months:
            for report in EXPECTED_REPORTS:
                if month.strftime("%Y-%m") < report["first_month"]:
                    continue

                if report["frequency"] == "monthly":
                    period = month
                    label = month.strftime("%b %Y")
                elif month.month in (3, 6, 9, 12):
                    period = month.asfreq("Q")
                    label = f"{period.start_time:%b}–{period.end_time:%b %Y}"
                else:
                    continue

                expected_count += 1
                if (report["name"], period) not in received:
                    missing.append({
                        "report": report["name"],
                        "provider": report["provider"],
                        "service_type": report["service_type"],
                        "frequency": report["frequency"],
                        "period": label,
                    })

        return DatasetResult(
            columns=["report", "provider", "service_type", "frequency", "period"],
            rows=[list(item.values()) for item in missing],
            row_count=len(missing),
            metadata={
                "dataset": self.id,
                "filters": parsed.model_dump(mode="json"),
                "expected_count": expected_count,
                "received_count": expected_count - len(missing),
                "missing": missing,
            },
        )
