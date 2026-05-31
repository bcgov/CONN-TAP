"""
Extract tables from Rogers professional_services.pdf.

Expected columns (headers repeat on every page):
  Title | Services Supported | Service ID | Business Hours Rate (Hourly) |
  After Business Hours Rate (Hourly) | Minimum Billing Increment | Fixed Fee
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

import pdfplumber

PROFESSIONAL_SERVICES_COLUMNS = [
    "pricebook_ingestion_run_id",
    "pdf_page_number",
    "title",
    "services_supported",
    "service_id",
    "business_hours_rate_hourly",
    "after_business_hours_rate_hourly",
    "minimum_billing_increment",
    "fixed_fee",
    "extras",
]

# Canonical header tokens used to detect header rows and map columns.
_HEADER_ALIASES: dict[str, str] = {
    "title": "title",
    "services_supported": "services_supported",
    "service_supported": "services_supported",
    "services supported": "services_supported",
    "service_id": "service_id",
    "service id": "service_id",
    "business_hours_rate_hourly": "business_hours_rate_hourly",
    "business hours rate hourly": "business_hours_rate_hourly",
    "after_business_hours_rate_hourly": "after_business_hours_rate_hourly",
    "after business hours rate hourly": "after_business_hours_rate_hourly",
    "minimum_billing_increment": "minimum_billing_increment",
    "minimum billing increment": "minimum_billing_increment",
    "fixed_fee": "fixed_fee",
    "fixed fee": "fixed_fee",
}

_REQUIRED_HEADER_FIELDS = frozenset({"title", "service_id"})

# Rogers professional services PDF column order (left to right).
_STANDARD_7_COL_LAYOUT = [
    "title",
    "services_supported",
    "service_id",
    "business_hours_rate_hourly",
    "after_business_hours_rate_hourly",
    "minimum_billing_increment",
    "fixed_fee",
]


def normalize_header_cell(value: Any) -> str:
    """Collapse PDF newlines and punctuation into a snake_case token."""
    if value is None:
        return ""
    s = str(value).replace("\u00a0", " ").replace("\n", " ").strip()
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s.lower())
    s = s.replace("(", " ").replace(")", " ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.replace(" ", "_")


def map_header_to_field(normalized: str) -> str:
    if not normalized:
        return ""
    if normalized in _HEADER_ALIASES:
        return _HEADER_ALIASES[normalized]
    # Fuzzy: strip parenthetical fragments already removed; match prefixes
    for key, field in _HEADER_ALIASES.items():
        if normalized == key.replace(" ", "_"):
            return field
    if "service_id" in normalized or normalized.endswith("_id") and "service" in normalized:
        return "service_id"
    if normalized.startswith("title"):
        return "title"
    if "services_supported" in normalized or "service_supported" in normalized:
        return "services_supported"
    if "business_hours" in normalized or (
        "business" in normalized and "hours" in normalized and "after" not in normalized
    ):
        return "business_hours_rate_hourly"
    if ("after" in normalized and "business" in normalized) or "after_business" in normalized:
        return "after_business_hours_rate_hourly"
    if ("minimum" in normalized and "billing" in normalized) or "billing_increment" in normalized:
        return "minimum_billing_increment"
    if "fixed" in normalized and "fee" in normalized:
        return "fixed_fee"
    if normalized in ("hourly", "rate_hourly") and "business" not in normalized:
        # Sub-header fragment on its own line; positional fallback fills the column.
        return ""
    return ""


def header_fields_from_row(row: list[Any]) -> list[str]:
    return [map_header_to_field(normalize_header_cell(c)) for c in row]


def is_header_row(row: list[Any]) -> bool:
    fields = {f for f in header_fields_from_row(row) if f}
    return _REQUIRED_HEADER_FIELDS <= fields


def is_subheader_row(row: list[Any]) -> bool:
    """Second header band row (rate / billing labels split below the main header)."""
    if row_is_empty(row):
        return False
    fields = {f for f in header_fields_from_row(row) if f}
    if fields & _REQUIRED_HEADER_FIELDS:
        return False
    texts = [normalize_header_cell(c) for c in row if normalize_header_cell(c)]
    if not texts:
        return False
    joined = " ".join(texts)
    return any(
        token in joined
        for token in (
            "rate",
            "hourly",
            "billing",
            "increment",
            "business",
            "after",
            "minimum",
            "fixed",
            "fee",
        )
    )


def merge_header_rows(row_a: list[Any], row_b: list[Any]) -> list[Any]:
    width = max(len(row_a), len(row_b))
    merged: list[Any] = []
    for i in range(width):
        parts: list[str] = []
        for row in (row_a, row_b):
            if i < len(row):
                text = as_cell_text(row[i])
                if text:
                    parts.append(text)
        merged.append(" ".join(parts) if parts else None)
    return merged


def apply_positional_fallback(col_fields: list[str]) -> list[str]:
    """Fill unmapped columns when the Rogers 7-column layout is recognized."""
    if len(col_fields) < 7:
        col_fields = col_fields + [""] * (7 - len(col_fields))
    fields = col_fields[:7]
    if fields[0] == "title" and fields[2] == "service_id":
        return [fields[i] or _STANDARD_7_COL_LAYOUT[i] for i in range(7)]
    return col_fields


def resolve_column_mapping(
    table: list[list[Any]], header_idx: int
) -> tuple[list[str], int]:
    """Build column field names and the first data row index."""
    header_row = table[header_idx]
    col_fields = header_fields_from_row(header_row)
    data_start = header_idx + 1

    if header_idx + 1 < len(table):
        next_row = table[header_idx + 1]
        if is_subheader_row(next_row):
            merged = merge_header_rows(header_row, next_row)
            merged_fields = header_fields_from_row(merged)
            if sum(1 for f in merged_fields if f) > sum(1 for f in col_fields if f):
                col_fields = merged_fields
                data_start = header_idx + 2

    col_fields = apply_positional_fallback(col_fields)
    return col_fields, data_start


def as_cell_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).replace("\u00a0", " ").replace("\n", " ").strip()
    s = re.sub(r"\s+", " ", s)
    if not s:
        return None
    return s


def row_is_empty(row: list[Any]) -> bool:
    return all(as_cell_text(c) is None for c in row)


def parse_table_rows(
    table: list[list[Any]],
    *,
    page_number: int,
) -> list[dict[str, Any]]:
    """Parse one pdfplumber table into data rows (headers stripped)."""
    if not table:
        return []

    # Find header row (first row that looks like the Rogers header band).
    header_idx: Optional[int] = None
    col_fields: list[str] = []
    data_start = 0
    for i, row in enumerate(table):
        if is_header_row(row):
            header_idx = i
            col_fields, data_start = resolve_column_mapping(table, i)
            break
    else:
        # No explicit header: assume first row is header if we have ~7 columns.
        if len(table) >= 2:
            col_fields = header_fields_from_row(table[0])
            if sum(1 for f in col_fields if f) >= 4:
                header_idx = 0
                col_fields, data_start = resolve_column_mapping(table, 0)
            else:
                return []
        else:
            return []

    if header_idx is None:
        return []

    out: list[dict[str, Any]] = []
    for row in table[data_start:]:
        if not row or row_is_empty(row):
            continue
        if is_header_row(row):
            continue

        vals: dict[str, Any] = {
            "pricebook_ingestion_run_id": None,
            "pdf_page_number": page_number,
            "extras": None,
        }
        extras: dict[str, str] = {}
        for idx, cell in enumerate(row):
            field = col_fields[idx] if idx < len(col_fields) else ""
            text = as_cell_text(cell)
            if not field:
                if text is not None:
                    extras[f"col_{idx}"] = text
                continue
            if field in PROFESSIONAL_SERVICES_COLUMNS:
                vals[field] = text
            else:
                extras[field] = text

        # Skip rows without a service id (section titles, footers).
        if not vals.get("service_id"):
            continue
        if extras:
            vals["extras"] = json.dumps(extras)
        out.append(vals)
    return out


def parse_rogers_professional_services_pdf(path: Path) -> list[dict[str, Any]]:
    """Return row dicts for all tables across all pages in the PDF."""
    rows: list[dict[str, Any]] = []
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables(
                table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "intersection_tolerance": 5,
                    "snap_tolerance": 3,
                }
            )
            if not tables:
                tables = page.extract_tables()
            for table in tables or []:
                rows.extend(parse_table_rows(table, page_number=page_num))
    return rows
