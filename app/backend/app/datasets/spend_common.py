"""Shared filter models and constants for spend datasets."""
from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, field_validator


class YearType(StrEnum):
    calendar = "calendar"
    fiscal = "fiscal"


class Filters(BaseModel):
    year_type: YearType = YearType.fiscal
    period: list[str] | None = None

    @field_validator("period", mode="before")
    @classmethod
    def parse_period_list(cls, value: Any) -> list[str] | None:
        if value is None or value == "" or value == []:
            return None
        if isinstance(value, list):
            parsed = [str(v) for v in value if v != ""]
            return parsed or None
        return [str(value)]


PROVIDER_ORDER = ("TELUS", "Rogers")
