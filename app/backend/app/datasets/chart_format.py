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
    """Format a spend figure, keeping small and negative amounts readable.

    Every non-null amount gets a label, down to cents and including an exact
    $0 — a category whose charges and credits cancel (Unknown, mostly Rogers
    late fees and their reversals) would otherwise render as a bar with no
    number, which reads as broken rather than as balanced. Callers pass None
    instead when a provider has no row at all; that is what stays unlabelled.
    """
    dollars = millions * 1_000_000
    magnitude = abs(dollars)
    if magnitude >= 1_000_000:
        figure = f"${magnitude / 1_000_000:.1f}M"
    elif magnitude >= 1_000:
        figure = f"${magnitude / 1_000:.1f}K"
    elif magnitude >= 1:
        figure = f"${magnitude:,.0f}"
    elif magnitude > 0:
        figure = f"${magnitude:.2f}"
    else:
        return "$0"
    # Accounting parentheses for credits: labels read "Rogers - $2.7K", so a
    # leading minus would render as "Rogers - -$2.7K".
    return f"({figure})" if dollars < 0 else figure
