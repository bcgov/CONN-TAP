"""Shared filter models for spend datasets."""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class YearType(StrEnum):
    calendar = "calendar"
    fiscal = "fiscal"


class Filters(BaseModel):
    year_type: YearType = YearType.fiscal
    year: int | None = None
    quarter: int | None = None
