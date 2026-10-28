"""TSMA section loader for the spend tracking workbook.

Reads TSMA monthly spend from the dbt report views (see report_source.py):

  rpt_tsma_monthly        -> per BGE: cellular, mms, data, voice, voice_ivr
  rpt_tsma_other_monthly  -> per BGE: Out of Scope (oos)
  rpt_tsma_lite_monthly   -> TSMA Lite, all added to School Districts

entity_key is the dbt BGE code; BGE_ROWS maps it to a workbook row.
"""

from __future__ import annotations

from datetime import datetime

from report_source import view_rows
from sheet_utils import FIRST_MONTH, LAST_MONTH, MONTH_COLS
from tsma_other import OOS_QUERY

# The report views have already resolved every raw organisation name to a BGE code
# (bge_alias_map). Only the dbt codes appear here;
# the workbook's VCHA block is keyed "VCHA".
BGE_ROWS = {
    "BC Hydro": "BC Hydro",
    "BCLC": "BCLC",
    "ECC": "ECC",
    "FHA": "FHA",
    "FNHA": "FNHA",
    "Gov BC": "Gov BC",
    "ICBC": "ICBC",
    "IHA": "IHA",
    "NHA": "NHA",
    "PHSA": "PHSA",
    "School Districts": "School Districts",
    "VCHA (+PHC)": "VCHA",
    "VIHA": "VIHA",
    "WSBC": "WSBC",
}

# One row per BGE and month (dbt view rpt_tsma_monthly); a column per workbook row type.
TSMA_QUERY = """
    SELECT entity_key, month_start,
           cellular_spend, mms_spend, data_spend, voice_spend, voice_ivr_spend, other_spend
    FROM intermediate.rpt_tsma_monthly
"""

TSMA_COMPONENT_COLS = {
    "cellular": "cellular_spend",
    "mms": "mms_spend",
    "data": "data_spend",
    "voice": "voice_spend",
    "voice_ivr": "voice_ivr_spend",
}

# One row per month (dbt view rpt_tsma_lite_monthly).
TSMA_LITE_QUERY = """
    SELECT month_start, conferencing_spend, long_distance_spend, voice_spend, cellular_spend, other_spend
    FROM intermediate.rpt_tsma_lite_monthly
"""

TSMA_LITE_COL_MAP = {
    "conferencing_spend": "conferencing",
    "long_distance_spend": "long_distance",
    "voice_spend": "voice",
    "cellular_spend": "cellular",
}


def _entity_key(value: object) -> str:
    return BGE_ROWS.get(str(value or "").strip(), "")


def _month_to_col(month_str: str):
    """Parse a month_start string -> 0-based Excel column, or None if out of range."""
    s = month_str.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y/%m/%d", "%Y/%m", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(s, fmt)
            col = FIRST_MONTH + (dt.year - 2024) * 12 + (dt.month - 1)
            return col if FIRST_MONTH <= col <= LAST_MONTH else None
        except ValueError:
            continue
    return None


def _amount(value: str) -> float | None:
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _outside_rows_total(query: str) -> float:
    """Spend the view reports in other_spend: a category with no workbook row (window months only)."""
    return sum(
        _amount(row.get("other_spend", "")) or 0.0
        for row in view_rows(query)
        if _month_to_col(row.get("month_start", "")) is not None
    )


def load_tsma_data() -> dict[tuple[str, str, int], float]:
    """Read the TSMA report views and return {(bge_name, row_type, col_idx): value}."""
    data: dict[tuple[str, str, int], float] = {}
    skipped: dict[tuple[str, str], float] = {}
    for row in view_rows(TSMA_QUERY):
        col = _month_to_col(row.get("month_start", ""))
        if col is None:
            continue
        for row_type, view_col in TSMA_COMPONENT_COLS.items():
            val = _amount(row.get(view_col, ""))
            if not val:
                continue
            bge = _entity_key(row.get("entity_key", ""))
            if not bge:
                # A BGE code with no workbook row: listed below so it can't go missing unnoticed.
                name = (row.get("entity_key") or "").strip() or "<blank>"
                skipped[(name, row_type)] = skipped.get((name, row_type), 0.0) + val
                continue
            key = (bge, row_type, col)
            data[key] = data.get(key, 0.0) + val
    for (name, row_type), total in sorted(skipped.items()):
        print(f"  ! TSMA: no workbook row for {name!r} ({row_type}); skipped {total:,.2f}")

    # Out of Scope: one row per feed / customer / BGE / month; entity_key is dbt's BGE.
    for row in view_rows(OOS_QUERY):
        try:
            col = FIRST_MONTH + (int(row.get("year_num", 0)) - 2024) * 12 + (int(row.get("month_num", 0)) - 1)
        except (TypeError, ValueError):
            continue
        val = _amount(row.get("total_billed_amt", ""))
        if not (FIRST_MONTH <= col <= LAST_MONTH) or val is None:
            continue
        bge = _entity_key(row.get("entity_key", ""))
        if not bge:
            name = (row.get("entity_key") or "").strip() or "<blank>"
            skipped[(name, "oos")] = skipped.get((name, "oos"), 0.0) + val
            continue
        key = (bge, "oos", col)
        data[key] = data.get(key, 0.0) + val
    for (name, row_type), total in sorted(skipped.items()):
        if row_type == "oos":
            print(f"  ! TSMA: no workbook row for {name!r} (oos); skipped {total:,.2f}")

    for label, query in (("TSMA", TSMA_QUERY), ("TSMA Lite", TSMA_LITE_QUERY)):
        outside = _outside_rows_total(query)
        if round(outside, 2):
            print(f"  ! {label}: {outside:,.2f} in a service category with no workbook row; not shown")

    for (lite_type, col), amount in load_tsma_lite_data().items():
        if lite_type == "cellular":
            row_type = "cellular"
        elif lite_type in ("conferencing", "long_distance", "voice"):
            row_type = "voice"
        else:
            continue
        key = ("School Districts", row_type, col)
        data[key] = data.get(key, 0.0) + amount

    return data


def load_tsma_lite_data() -> dict[tuple[str, int], float]:
    """Read rpt_tsma_lite_monthly and return {(row_type, col_idx): value}."""
    data: dict[tuple[str, int], float] = {}
    for row in view_rows(TSMA_LITE_QUERY):
        col = _month_to_col(row.get("month_start", ""))
        if col is None:
            continue
        for view_col, row_type in TSMA_LITE_COL_MAP.items():
            val = _amount(row.get(view_col, ""))
            if val is None:
                continue
            key = (row_type, col)
            data[key] = data.get(key, 0.0) + val

    return data


def write_tsma_detail_row(ws, row_num: int, col_fmt, tsma_data: dict, bge_name: str, row_type: str) -> None:
    for col in MONTH_COLS:
        amount = tsma_data.get((bge_name, row_type, col), 0)
        ws.write_number(row_num - 1, col, round(amount, 2), col_fmt)
