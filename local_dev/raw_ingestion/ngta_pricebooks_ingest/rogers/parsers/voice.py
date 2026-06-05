"""
Extract tables from Rogers voice.pdf.

Table 1 (base_service, pages 1–2): Service ID | Service Name | Service Component |
  Monthly Fixed Fee | CPM Rate | ECF Rate | ECF Unit of Measure

Table 2 (long_distance): Service ID | Service Subcategory | Service Component |
  CPM Rate | Terminating Country | ECF Rate
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal, Optional

import pdfplumber

VoiceTableSection = Literal["base_service", "long_distance"]

VOICE_COLUMNS = [
    "pricebook_ingestion_run_id",
    "pdf_page_number",
    "voice_table_section",
    "service_id",
    "service_name",
    "service_subcategory",
    "service_component",
    "monthly_fixed_fee",
    "cpm_rate",
    "terminating_country",
    "ecf_rate",
    "ecf_unit_of_measure",
    "extras",
]

_HEADER_ALIASES: dict[str, str] = {
    "service_id": "service_id",
    "service id": "service_id",
    "service_name": "service_name",
    "service name": "service_name",
    "service_subcategory": "service_subcategory",
    "service subcategory": "service_subcategory",
    "service_component": "service_component",
    "service component": "service_component",
    "monthly_fixed_fee": "monthly_fixed_fee",
    "monthly fixed fee": "monthly_fixed_fee",
    "cpm_rate": "cpm_rate",
    "cpm rate": "cpm_rate",
    "ecf_rate": "ecf_rate",
    "ecf rate": "ecf_rate",
    "ecf_unit_of_measure": "ecf_unit_of_measure",
    "ecf unit of measure": "ecf_unit_of_measure",
    "terminating_country": "terminating_country",
    "terminating country": "terminating_country",
}

_TABLE1_LAYOUT = [
    "service_id",
    "service_name",
    "service_component",
    "monthly_fixed_fee",
    "cpm_rate",
    "ecf_rate",
    "ecf_unit_of_measure",
]

_TABLE2_LAYOUT = [
    "service_id",
    "service_subcategory",
    "service_component",
    "cpm_rate",
    "terminating_country",
    "ecf_rate",
]

_TABLE1_LEADING = 3
_TABLE1_TAIL = _TABLE1_LAYOUT[_TABLE1_LEADING:]

_TABLE2_LEADING = 3
_TABLE2_TAIL = _TABLE2_LAYOUT[_TABLE2_LEADING:]


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
    if "subcategory" in normalized:
        return "service_subcategory"
    if "service_name" in normalized or (
        normalized.startswith("service") and "name" in normalized and "subcategory" not in normalized
    ):
        return "service_name"
    if "service_component" in normalized or (
        "component" in normalized and "service" in normalized
    ):
        return "service_component"
    if "monthly" in normalized and "fee" in normalized:
        return "monthly_fixed_fee"
    if normalized == "cpm" or ("cpm" in normalized and "rate" in normalized):
        return "cpm_rate"
    if "terminating" in normalized and "country" in normalized:
        return "terminating_country"
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
    if "service_id" not in fields:
        return False
    if "service_name" in fields:
        return True
    if "service_subcategory" in fields or "terminating_country" in fields:
        return True
    return False


def is_subheader_row(row: list[Any]) -> bool:
    if row_is_empty(row):
        return False
    fields = {f for f in header_fields_from_row(row) if f}
    if "service_id" in fields and (
        "service_name" in fields
        or "service_subcategory" in fields
        or "terminating_country" in fields
    ):
        return False
    texts = [normalize_header_cell(c) for c in row if normalize_header_cell(c)]
    if not texts:
        return False
    joined = " ".join(texts)
    return any(
        token in joined
        for token in (
            "monthly",
            "ecf",
            "fee",
            "rate",
            "cpm",
            "measure",
            "fixed",
            "unit",
            "terminating",
            "country",
            "subcategory",
        )
    )


def classify_voice_table(col_fields: list[str]) -> Optional[VoiceTableSection]:
    fields = {f for f in col_fields if f}
    if "service_id" not in fields:
        return None
    if "terminating_country" in fields or "service_subcategory" in fields:
        return "long_distance"
    if "service_name" in fields:
        return "base_service"
    if "cpm_rate" in fields and "monthly_fixed_fee" not in fields:
        return "long_distance"
    return None


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


def _apply_wide_layout_base_service(col_fields: list[str]) -> list[str]:
    """PDFs often insert an extra column between name and component."""
    width = len(col_fields)
    tail = _TABLE1_TAIL
    min_wide = 1 + 1 + 1 + len(tail)  # id + name + component + tail
    if width < min_wide or col_fields[0] != "service_id":
        return col_fields

    result = _pad_col_fields(col_fields, width)
    result[0] = "service_id"
    result[1] = "service_name"
    for offset, name in enumerate(tail):
        result[width - len(tail) + offset] = name
    middle_end = width - len(tail)
    for idx in range(2, middle_end):
        result[idx] = "service_component"
    return result


def _apply_wide_layout_long_distance(col_fields: list[str]) -> list[str]:
    width = len(col_fields)
    tail = _TABLE2_TAIL
    min_wide = _TABLE2_LEADING + len(tail) + 1
    if width < min_wide or col_fields[0] != "service_id":
        return col_fields

    result = _pad_col_fields(col_fields, width)
    result[0] = "service_id"
    result[1] = "service_subcategory"
    for offset, name in enumerate(tail):
        result[width - len(tail) + offset] = name
    for idx in range(2, width - len(tail)):
        if not result[idx] or result[idx] not in VOICE_COLUMNS:
            result[idx] = "service_component"
    return result


def finalize_mapping(
    col_fields: list[str], section: VoiceTableSection
) -> list[str]:
    if section == "base_service":
        layout = _TABLE1_LAYOUT
    else:
        layout = _TABLE2_LAYOUT

    width = len(col_fields)
    if width > len(layout) and col_fields[0] == "service_id":
        if section == "base_service":
            return _apply_wide_layout_base_service(_pad_col_fields(col_fields, width))
        return _apply_wide_layout_long_distance(_pad_col_fields(col_fields, width))

    if width < len(layout):
        col_fields = _pad_col_fields(col_fields, len(layout))
    fields = col_fields[: len(layout)]
    if fields[0] == "service_id":
        return [fields[i] or layout[i] for i in range(len(layout))]
    return col_fields


def resolve_column_mapping(
    table: list[list[Any]], header_idx: int
) -> tuple[list[str], int, Optional[VoiceTableSection]]:
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
    section = classify_voice_table(col_fields)
    if section is None:
        return col_fields, data_start, None
    return finalize_mapping(col_fields, section), data_start, section


def _apply_extras_tail_fallback(
    vals: dict[str, Any],
    extras: dict[str, str],
    col_fields: list[str],
    tail_fields: list[str],
) -> None:
    width = len(col_fields)
    for offset, field in enumerate(tail_fields):
        if vals.get(field):
            continue
        idx = width - len(tail_fields) + offset
        text = extras.pop(f"col_{idx}", None)
        if text:
            vals[field] = text


def row_to_record(
    row: list[Any],
    col_fields: list[str],
    *,
    page_number: int,
    voice_table_section: VoiceTableSection,
) -> Optional[dict[str, Any]]:
    vals: dict[str, Any] = {
        "pricebook_ingestion_run_id": None,
        "pdf_page_number": page_number,
        "voice_table_section": voice_table_section,
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
        if field in VOICE_COLUMNS:
            if text:
                multi.setdefault(field, []).append(text)
        elif text is not None:
            extras[field] = text

    for field, texts in multi.items():
        if field == "service_component":
            vals[field] = next((t for t in reversed(texts) if t), texts[0])
        else:
            vals[field] = texts[0]

    tail = _TABLE1_TAIL if voice_table_section == "base_service" else _TABLE2_TAIL
    _apply_extras_tail_fallback(vals, extras, col_fields, tail)

    if voice_table_section == "base_service" and not vals.get("service_component"):
        for key in ("col_3", "col_2"):
            text = extras.pop(key, None)
            if text:
                vals["service_component"] = text
                break

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
    section: Optional[VoiceTableSection] = None

    for i, row in enumerate(table):
        if is_header_row(row):
            header_idx = i
            col_fields, data_start, section = resolve_column_mapping(table, i)
            break
    else:
        if len(table) >= 2:
            probe = header_fields_from_row(table[0])
            if sum(1 for f in probe if f) >= 3 and is_header_row(table[0]):
                header_idx = 0
                col_fields, data_start, section = resolve_column_mapping(table, 0)
            else:
                return []
        else:
            return []

    if header_idx is None or section is None:
        return []

    out: list[dict[str, Any]] = []
    i = data_start
    while i < len(table):
        row = table[i]
        if not row or row_is_empty(row):
            i += 1
            continue
        if is_header_row(row):
            col_fields, data_start, section = resolve_column_mapping(table, i)
            if section is None:
                i += 1
                continue
            i = data_start
            continue
        record = row_to_record(
            row, col_fields, page_number=page_number, voice_table_section=section
        )
        i += 1
        if record is None:
            continue
        out.append(record)
    return out


def parse_rogers_voice_pdf(path: Path) -> list[dict[str, Any]]:
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
