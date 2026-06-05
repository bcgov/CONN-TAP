"""Pydantic schemas for the ISP spending dataset."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Filters(BaseModel):
    region: str | None = None
    year: int | None = Field(default=None, ge=1900, le=2100)
    limit: int = Field(default=1000, ge=1, le=100_000)


class Row(BaseModel):
    region: str
    year: int | None = None
    total_spend: float
    line_items: int | None = None
