"""Shared chart formatting utilities."""
from __future__ import annotations

from decimal import Decimal
from typing import Any


def to_float(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)
    if value is None:
        return 0.0
    return float(value)


def fmt_spend(millions: float) -> str:
    if millions == 0:
        return ""
    if millions >= 1:
        return f"${millions:.1f}M"
    thousands = millions * 1000
    if thousands >= 1:
        return f"${thousands:.1f}K"
    return f"${millions * 1_000_000:,.0f}"
