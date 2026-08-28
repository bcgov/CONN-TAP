"""Shared filter models and constants for spend datasets."""
from __future__ import annotations

from typing import Any

import pandas as pd
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session


class Filters(BaseModel):
    #: Months to include, as `YYYY-MM` (the grain the timeline selector emits).
    period: list[str] | None = None

    @field_validator("period", mode="before")
    @classmethod
    def parse_str_list(cls, value: Any) -> list[str] | None:
        if value is None or value == "" or value == []:
            return None
        if isinstance(value, list):
            parsed = [str(v) for v in value if v != ""]
            return parsed or None
        return [str(value)]


PROVIDER_ORDER = ("TELUS", "Rogers")


def pg_text_array(values: list[str] | None) -> str | None:
    return "{" + ",".join(values) + "}" if values else None


def run_period_query(service: Any, db: Session, filters: Filters) -> pd.DataFrame:
    return service.execute_sql(
        db,
        "spend",
        params={"period": pg_text_array(filters.period)},
    )
