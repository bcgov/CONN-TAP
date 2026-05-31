"""
Extract tables from Rogers cellular.pdf.

Expected columns (headers repeat on every page):
  Service ID | Service Name | Service Component | Speed Mbps or Capacity MB |
  Monthly Fixed Fee | ECF Rate | RLH USA Overage Fee | RLH Intl Overage Fee |
  ECF Unit of Measure | Fixed Fee | Overage Charge
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

import pdfplumber

CELLULAR_COLUMNS = [
    "pricebook_ingestion_run_id",
    "pdf_page_number",
    "service_id",
    "service_name",
    "service_component",
    "speed_mbps_or_capacity_mb",
    "monthly_fixed_fee",
    "ecf_rate",
    "rlh_roam_like_home_usa_overage_fee",
    "rlh_roam_like_home_intl_overage_fee",
    "ecf_unit_of_measure",
    "fixed_fee",
    "overage_charge",
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
    "rlh_roam_like_home_usa_overage_fee": "rlh_roam_like_home_usa_overage_fee",
    "rlh_roam_like_home_intl_overage_fee": "rlh_roam_like_home_intl_overage_fee",
    "ecf_unit_of_measure": "ecf_unit_of_measure",
    "ecf unit of measure": "ecf_unit_of_measure",
    "fixed_fee": "fixed_fee",
    "fixed fee": "fixed_fee",
    "overage_charge": "overage_charge",
    "overage charge": "overage_charge",
}

_REQUIRED_HEADER_FIELDS = frozenset({"service_id", "service_name"})

_STANDARD_11_COL_LAYOUT = [
    "service_id",
    "service_name",
    "service_component",
    "speed_mbps_or_capacity_mb",
    "monthly_fixed_fee",
    "ecf_rate",
    "rlh_roam_like_home_usa_overage_fee",
    "rlh_roam_like_home_intl_overage_fee",
    "ecf_unit_of_measure",
    "fixed_fee",
    "overage_charge",
]

_NUM_LEADING = 3
_TAIL_FIELDS = _STANDARD_11_COL_LAYOUT[_NUM_LEADING + 1 :]
_NUM_TAIL = len(_TAIL_FIELDS)


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
    if "service_component" in normalized or (
        "component" in normalized and "service" in normalized
    ):
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
    if "rlh" in normalized or "roam_like_home" in normalized or "roam" in normalized:
        if "usa" in normalized or "u_s_a" in normalized:
            return "rlh_roam_like_home_usa_overage_fee"
        if "intl" in normalized or "international" in normalized:
            return "rlh_roam_like_home_intl_overage_fee"
    if "overage" in normalized and "charge" in normalized:
        return "overage_charge"
    if "fixed" in normalized and "fee" in normalized:
        return "fixed_fee"
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
        for token in (
            "speed",
            "mbps",
            "capacity",
            "monthly",
            "ecf",
            "fee",
            "rate",
            "measure",
            "rlh",
            "roam",
            "overage",
            "intl",
            "usa",
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


def _pad_col_fields(col_fields: list[str], width: int) -> list[str]:
    if len(col_fields) < width:
        return col_fields + [""] * (width - len(col_fields))
    return list(col_fields)


def apply_wide_table_layout(col_fields: list[str]) -> list[str]:
    """Speed header split pushes fee / RLH columns to the right."""
    width = len(col_fields)
    min_wide = _NUM_LEADING + _NUM_TAIL + 1
    if width < min_wide:
        return col_fields
    if col_fields[0] != "service_id" or col_fields[1] != "service_name":
        return col_fields

    result = _pad_col_fields(col_fields, width)
    result[0] = "service_id"
    result[1] = "service_name"
    if not result[2]:
        result[2] = "service_component"

    for offset, name in enumerate(_TAIL_FIELDS):
        result[width - _NUM_TAIL + offset] = name

    for idx in range(_NUM_LEADING, width - _NUM_TAIL):
        mapped = result[idx]
        if mapped in ("", "service_component") or mapped not in CELLULAR_COLUMNS:
            result[idx] = "speed_mbps_or_capacity_mb"

    return result


def finalize_column_mapping(col_fields: list[str]) -> list[str]:
    width = len(col_fields)
    if width > len(_STANDARD_11_COL_LAYOUT) and col_fields[0] == "service_id" and col_fields[1] == "service_name":
        return apply_wide_table_layout(_pad_col_fields(col_fields, width))

    if width < len(_STANDARD_11_COL_LAYOUT):
        col_fields = _pad_col_fields(col_fields, len(_STANDARD_11_COL_LAYOUT))
    fields = col_fields[: len(_STANDARD_11_COL_LAYOUT)]
    if fields[0] == "service_id" and fields[1] == "service_name":
        return [fields[i] or _STANDARD_11_COL_LAYOUT[i] for i in range(len(_STANDARD_11_COL_LAYOUT))]
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


def _pick_speed_value(candidates: list[str]) -> Optional[str]:
    if not candidates:
        return None
    for text in candidates:
        if re.fullmatch(r"[\d.,]+", text.replace(",", "")):
            return text
    return candidates[0]


def _apply_extras_tail_fallback(
    vals: dict[str, Any],
    extras: dict[str, str],
    col_fields: list[str],
) -> None:
    width = len(col_fields)
    for offset, field in enumerate(_TAIL_FIELDS):
        if vals.get(field):
            continue
        idx = width - _NUM_TAIL + offset
        text = extras.pop(f"col_{idx}", None)
        if text:
            vals[field] = text


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
        if field in CELLULAR_COLUMNS:
            if text:
                multi.setdefault(field, []).append(text)
        elif text is not None:
            extras[field] = text

    for field, texts in multi.items():
        if field == "speed_mbps_or_capacity_mb":
            vals[field] = _pick_speed_value(texts)
        else:
            vals[field] = texts[0]

    _apply_extras_tail_fallback(vals, extras, col_fields)

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


def parse_rogers_cellular_pdf(path: Path) -> list[dict[str, Any]]:
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
