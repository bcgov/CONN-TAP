"""
Extract tables from Rogers data.pdf.

Expected columns (headers repeat on every page):
  Service ID | Service Name | Service Component | Speed Mbps or Capacity MB |
  Monthly Fixed Fee | ECF Rate | ECF Unit of Measure
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

import pdfplumber

DATA_COLUMNS = [
    "pricebook_ingestion_run_id",
    "pdf_page_number",
    "service_id",
    "service_name",
    "service_component",
    "speed_mbps_or_capacity_mb",
    "monthly_fixed_fee",
    "ecf_rate",
    "ecf_unit_of_measure",
    "extras",
]

_HEADER_ALIASES: dict[str, str] = {
    "service_id": "service_id",
    "service id": "service_id",
    "service_name": "service_name",
    "service name": "service_name",
    "service_component": "service_component",
    "service component": "service_component",
    "speed_mbps_or_capacity_mb": "speed_mbps_or_capacity_mb",
    "speed mbps or capacity mb": "speed_mbps_or_capacity_mb",
    "monthly_fixed_fee": "monthly_fixed_fee",
    "monthly fixed fee": "monthly_fixed_fee",
    "ecf_rate": "ecf_rate",
    "ecf rate": "ecf_rate",
    "ecf_unit_of_measure": "ecf_unit_of_measure",
    "ecf unit of measure": "ecf_unit_of_measure",
}

_REQUIRED_HEADER_FIELDS = frozenset({"service_id", "service_name"})

_STANDARD_7_COL_LAYOUT = [
    "service_id",
    "service_name",
    "service_component",
    "speed_mbps_or_capacity_mb",
    "monthly_fixed_fee",
    "ecf_rate",
    "ecf_unit_of_measure",
]


def normalize_header_cell(value: Any) -> str:
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
    if "service_id" in normalized or (normalized.endswith("_id") and "service" in normalized):
        return "service_id"
    if "service_name" in normalized or (
        normalized.startswith("service") and "name" in normalized and "component" not in normalized
    ):
        return "service_name"
    if "service_component" in normalized or "component" in normalized:
        return "service_component"
    if ("speed" in normalized and ("mbps" in normalized or "capacity" in normalized)) or (
        "mbps" in normalized and "mb" in normalized
    ):
        return "speed_mbps_or_capacity_mb"
    if normalized in ("mbps", "mb", "or", "capacity") or normalized.startswith("or_"):
        return "speed_mbps_or_capacity_mb"
    if "monthly" in normalized and "fee" in normalized:
        return "monthly_fixed_fee"
    if "ecf" in normalized and "rate" in normalized:
        return "ecf_rate"
    if "ecf" in normalized and ("unit" in normalized or "measure" in normalized):
        return "ecf_unit_of_measure"
    return ""


def header_fields_from_row(row: list[Any]) -> list[str]:
    return [map_header_to_field(normalize_header_cell(c)) for c in row]


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


def is_header_row(row: list[Any]) -> bool:
    fields = {f for f in header_fields_from_row(row) if f}
    return _REQUIRED_HEADER_FIELDS <= fields


def is_subheader_row(row: list[Any]) -> bool:
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
        for token in ("speed", "mbps", "capacity", "monthly", "ecf", "fee", "rate", "measure")
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


def _pad_col_fields(col_fields: list[str], width: int) -> list[str]:
    if len(col_fields) < width:
        return col_fields + [""] * (width - len(col_fields))
    return list(col_fields)


def apply_wide_table_layout(col_fields: list[str]) -> list[str]:
    """
    Rogers data.pdf often extracts 10+ columns: speed header is split across
  several cells, pushing Monthly Fixed Fee / ECF to col_8+.
    """
    width = len(col_fields)
    if width <= 7:
        return col_fields
    if col_fields[0] != "service_id" or col_fields[1] != "service_name":
        return col_fields

    result = _pad_col_fields(col_fields, width)
    result[0] = "service_id"
    result[1] = "service_name"
    if not result[2]:
        result[2] = "service_component"

    tail = ("monthly_fixed_fee", "ecf_rate", "ecf_unit_of_measure")
    for offset, name in enumerate(tail):
        result[width - 3 + offset] = name

    for idx in range(3, width - 3):
        mapped = result[idx]
        if mapped in ("", "service_component") or mapped not in DATA_COLUMNS:
            result[idx] = "speed_mbps_or_capacity_mb"

    return result


def finalize_column_mapping(col_fields: list[str]) -> list[str]:
    width = len(col_fields)
    if width > 7 and col_fields[0] == "service_id" and col_fields[1] == "service_name":
        merged_header = apply_wide_table_layout(_pad_col_fields(col_fields, width))
        # Fill any leading gaps from partial header detection.
        if merged_header[0] == "service_id" and merged_header[1] == "service_name":
            for i, name in enumerate(_STANDARD_7_COL_LAYOUT):
                if i < len(merged_header) and not merged_header[i]:
                    merged_header[i] = name
        return merged_header

    if width < 7:
        col_fields = _pad_col_fields(col_fields, 7)
    fields = col_fields[:7]
    if fields[0] == "service_id" and fields[1] == "service_name":
        return [fields[i] or _STANDARD_7_COL_LAYOUT[i] for i in range(7)]
    return col_fields


def resolve_column_mapping(
    table: list[list[Any]], header_idx: int
) -> tuple[list[str], int]:
    header_row = table[header_idx]
    col_fields = header_fields_from_row(header_row)
    data_start = header_idx + 1
    header_width = len(header_row)

    if header_idx + 1 < len(table):
        next_row = table[header_idx + 1]
        if is_subheader_row(next_row):
            merged = merge_header_rows(header_row, next_row)
            merged_fields = header_fields_from_row(merged)
            header_width = max(header_width, len(merged), len(next_row))
            if sum(1 for f in merged_fields if f) > sum(1 for f in col_fields if f):
                col_fields = merged_fields
                data_start = header_idx + 2

    col_fields = _pad_col_fields(col_fields, header_width)
    return finalize_column_mapping(col_fields), data_start


def _first_non_empty(row: list[Any], indices: list[int]) -> Optional[str]:
    for idx in indices:
        if idx < len(row):
            text = as_cell_text(row[idx])
            if text:
                return text
    return None


def _pick_speed_value(candidates: list[str]) -> Optional[str]:
    if not candidates:
        return None
    for text in candidates:
        if re.fullmatch(r"[\d.,]+", text.replace(",", "")):
            return text
    return candidates[0]


def row_to_record(
    row: list[Any],
    col_fields: list[str],
    *,
    page_number: int,
) -> Optional[dict[str, Any]]:
    vals: dict[str, Any] = {
        "pricebook_ingestion_run_id": None,
        "pdf_page_number": page_number,
        "extras": None,
    }
    extras: dict[str, str] = {}
    multi: dict[str, list[str]] = {}

    for idx, cell in enumerate(row):
        field = col_fields[idx] if idx < len(col_fields) else ""
        text = as_cell_text(cell)
        if not field:
            if text is not None:
                extras[f"col_{idx}"] = text
            continue
        if field in DATA_COLUMNS:
            if text:
                multi.setdefault(field, []).append(text)
        elif text is not None:
            extras[field] = text

    for field, texts in multi.items():
        if field == "speed_mbps_or_capacity_mb":
            vals[field] = _pick_speed_value(texts)
        else:
            vals[field] = texts[0]

    # Fee columns landed in extras (col_8+) when mapping was still wrong.
    if not vals.get("monthly_fixed_fee") and extras:
        fee = extras.pop("col_8", None)
        if fee:
            vals["monthly_fixed_fee"] = fee
    if not vals.get("ecf_rate") and extras:
        rate = extras.pop("col_9", None)
        if rate:
            vals["ecf_rate"] = rate
    if not vals.get("ecf_unit_of_measure") and extras:
        uom = extras.pop("col_10", None)
        if uom:
            vals["ecf_unit_of_measure"] = uom

    if not vals.get("service_id"):
        return None
    if extras:
        vals["extras"] = json.dumps(extras)
    return vals


def parse_table_rows(
    table: list[list[Any]],
    *,
    page_number: int,
) -> list[dict[str, Any]]:
    if not table:
        return []

    header_idx: Optional[int] = None
    col_fields: list[str] = []
    data_start = 0
    for i, row in enumerate(table):
        if is_header_row(row):
            header_idx = i
            col_fields, data_start = resolve_column_mapping(table, i)
            break
    else:
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

        record = row_to_record(row, col_fields, page_number=page_number)
        if record is None:
            continue
        out.append(record)
    return out


def parse_rogers_data_pdf(path: Path) -> list[dict[str, Any]]:
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
