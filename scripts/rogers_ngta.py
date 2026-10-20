"""Rogers NGTA section - CSV ingestion and worksheet section writer.

The section builder is parameterised by `first_row` so it can be embedded
inside the full spend_tracking workbook (first_row=232) or written as a
standalone file (first_row=5, after four rows of month/quarter headers).

Row layout relative to first_row
---------------------------------
  first_row + 0     : Rogers NGTA header
  first_row + 1-5   : Summary rows (Cellular Plans / H/W / Data / Voice / Other)
  first_row + 6     : Summary Total  ← returned by build_rogers_ngta_section()
  first_row + 7     : BGEs header (outline level 1)
  first_row + 8     : first BGE data row
  first_row + 91    : last BGE data row (14 BGEs × 6 rows)
  first_row + 92-96 : aggregate TOTAL rows (outline level 1)
  first_row + 97    : hidden separator
  first_row + 98-102 : hidden Gov & ECC sub-totals
  first_row + 103   : hidden separator
  first_row + 104-108: hidden Health sub-totals
  first_row + 109   : hidden separator
  first_row + 110-114: hidden Crown Corps sub-totals
  first_row + 115   : hidden separator
  first_row + 116-120: hidden School Districts sub-totals
  first_row + 122   : cyan separator (omitted when include_separator=False)
"""

import csv
import os
import re
from datetime import datetime

from sheet_utils import (
    BG_ROGERS_HDR, BG_ROGERS_BGE, BG_SEPARATOR,
    COL_A, COL_B, COL_AM, COL_AN, COL_AO, COL_AP, COL_AR, COL_AS,
    MONTH_COLS, FIRST_MONTH, LAST_MONTH, Y2024, Y2025,
    BGES, BGE_A_LABELS, BGE_A2_LABELS, NGTA_BGE_ROWS,
    _build_ngta_row_map, _ngta_rows_by_type,
    col_letter, annual_sum, q_sum,
    write, write_f, set_row_props,
    write_monthly_formula, write_monthly_ref,
    write_monthly_sum_rows, write_monthly_sum_range,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SOURCE_DIR  = os.path.join(os.path.dirname(__file__), "source")
ROGERS_CSV  = os.path.join(SOURCE_DIR, "rogers_ngta_spend.csv")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "rogers_ngta_spend.xlsx")

# ---------------------------------------------------------------------------
# BGE code -> workbook row
# ---------------------------------------------------------------------------
# rogers.sql reads the dbt view rpt_rogers_ngta_monthly, which has already resolved every
# raw Rogers name to a BGE code (bge_alias_map / sub_bge_alias_map). Only the dbt codes
# appear here; the workbook's VCHA block is keyed "VCHA".
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

# Maps CSV column names → NGTA_BGE_ROWS row-type keys
SPEND_COL_MAP = {
    "cellular_plans":    "cell_plans",
    "cellular_hardware": "cell_hw",
    "data_spend":        "data",
    "voice_spend":       "voice",
    "other_spend":       "other",
}

# ---------------------------------------------------------------------------
# CSV ingestion
# ---------------------------------------------------------------------------

def _header_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _resolve_bge(row: dict[str, str]) -> str:
    return BGE_ROWS.get(str(row.get("entity_key") or "").strip(), "")


def _month_to_col(month_str: str):
    """Parse a month string to a 0-based Excel column, or None if out of range."""
    s = str(month_str).strip()
    if not s:
        return None
    for fmt in (
        "%Y-%m-%d", "%Y-%m", "%Y/%m/%d", "%Y/%m",
        "%m/%d/%Y", "%d/%m/%Y", "%b %Y", "%B %Y",
    ):
        try:
            dt = datetime.strptime(s, fmt)
            col = FIRST_MONTH + (dt.year - 2024) * 12 + (dt.month - 1)
            return col if FIRST_MONTH <= col <= LAST_MONTH else None
        except ValueError:
            continue
    return None


def _amount(value: object) -> float | None:
    raw = str(value).strip()
    if not raw:
        return None
    raw = raw.replace("$", "").replace(",", "")
    if raw.startswith("(") and raw.endswith(")"):
        raw = "-" + raw[1:-1]
    try:
        return float(raw)
    except ValueError:
        return None


def _first_value(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    return ""


def _read_rows(path: str):
    if not os.path.exists(path):
        return

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        reader.fieldnames = [_header_key(h) for h in (reader.fieldnames or [])]
        yield from reader


def _add(
    data: dict[tuple[str, str, int], float],
    bge: str,
    row_type: str,
    col: int,
    value: float | None,
) -> None:
    if value is None:
        return
    key = (bge, row_type, col)
    data[key] = data.get(key, 0.0) + value


def load_rogers_ngta(path: str = ROGERS_CSV) -> dict[tuple[str, str, int], float]:
    """Read rogers_ngta_spend.csv (the output of scripts/sql/rogers.sql) and return
    {(bge_key, row_type, col_idx): value}.

    One CSV row per BGE and month. Months outside 2024-2026 are skipped. A BGE code
    with no workbook row is skipped too, but listed on stdout so it can't go missing
    unnoticed. Values for the same (bge, row_type, col) are summed.
    """
    data: dict[tuple[str, str, int], float] = {}
    skipped: dict[str, float] = {}
    for row in _read_rows(path) or ():
        col = _month_to_col(_first_value(row, "month_start", "month"))
        if col is None:
            continue
        bge = _resolve_bge(row)
        if not bge:
            key = row.get("entity_key") or "<blank>"
            skipped[key] = skipped.get(key, 0.0) + (_amount(row.get("total_reported", "")) or 0.0)
            continue
        for csv_col, row_type in SPEND_COL_MAP.items():
            _add(data, bge, row_type, col, _amount(row.get(csv_col, "")))
    for key, total in sorted(skipped.items()):
        print(f"  ! Rogers: no workbook row for BGE {key!r}; skipped {total:,.2f}")
    return data


# ---------------------------------------------------------------------------
# Section builder
# ---------------------------------------------------------------------------

_SPEND_TYPES = [
    ("Cellular",     "cell_plans"),
    ("Cellular H/W", "cell_hw"),
    ("Data",         "data"),
    ("Voice",        "voice"),
    ("Other",        "other"),
]


def build_rogers_ngta_section(ws, F, rogers_data: dict, *,
                               first_row: int = 232,
                               include_separator: bool = True) -> int:
    """Write the complete Rogers NGTA section to *ws* starting at *first_row*.

    Args:
        ws:                xlsxwriter Worksheet.
        F:                 _FmtCache instance bound to the workbook.
        rogers_data:       dict returned by load_rogers_ngta().
        first_row:         Row number of the Rogers NGTA header (1-based).
                           Use 232 in the full spend_tracking sheet,
                           use 5 in the standalone rogers_ngta_spend sheet.
        include_separator: Write the cyan separator row at the very end.

    Returns:
        The row number of the summary "Total" row so callers can reference
        it in combined-total formulas.
    """
    # ---- derive all section-relative row positions ----
    bges_data_start = first_row + 8
    rogers_row_map, tot_start = _build_ngta_row_map(bges_data_start)

    tot_plans = tot_start
    tot_hw    = tot_start + 1
    tot_dat   = tot_start + 2
    tot_voi   = tot_start + 3
    tot_oth   = tot_start + 4

    plans_rows = _ngta_rows_by_type(rogers_row_map, "cell_plans")
    hw_rows    = _ngta_rows_by_type(rogers_row_map, "cell_hw")
    dat_rows   = _ngta_rows_by_type(rogers_row_map, "data")
    voi_rows   = _ngta_rows_by_type(rogers_row_map, "voice")
    oth_rows   = _ngta_rows_by_type(rogers_row_map, "other")

    _frogh   = F.n(bg_color=BG_ROGERS_HDR)
    _frogh_b = F.n(bold=True, bg_color=BG_ROGERS_HDR)
    _frogb   = F.n(bg_color=BG_ROGERS_BGE)
    _frogb_b = F.n(bold=True, bg_color=BG_ROGERS_BGE)
    _collapsed = {"level": 1, "hidden": True}
    _hidden  = {"hidden": True}

    # ---- section header ----
    set_row_props(ws, first_row, height=16, fmt=_frogh)
    write(ws, first_row, COL_B, "Rogers NGTA", _frogh_b)

    # ---- summary rows (plans / hw / data / voice / other) ----
    sum_start = first_row + 1
    for i, (label, tot_row) in enumerate([
        ("Cellular Plans", tot_plans),
        ("Cellular H/W",   tot_hw),
        ("Data",           tot_dat),
        ("Voice",          tot_voi),
        ("Other",          tot_oth),
    ]):
        r = sum_start + i
        set_row_props(ws, r, height=17, fmt=_frogh)
        write(ws, r, COL_B, label, _frogh)
        write_monthly_ref(ws, r, tot_row, _frogh)
        write(ws, r, COL_AN, label)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # ---- summary Total row ----
    sum_total_r = sum_start + 5
    set_row_props(ws, sum_total_r, height=17, fmt=_frogh, opts={"collapsed": True})
    write(ws, sum_total_r, COL_B, "Total", _frogh_b)
    write_monthly_sum_range(ws, sum_total_r, sum_start, sum_start + 4, _frogh_b)

    # ---- BGEs header ----
    bges_hdr = first_row + 7
    set_row_props(ws, bges_hdr, fmt=_frogh, opts=_collapsed)
    write(ws, bges_hdr, COL_A, "BGEs", _frogh_b)

    # ---- BGE detail rows ----
    for bge_name, a_label, a2_label in zip(BGES, BGE_A_LABELS, BGE_A2_LABELS):
        bge_key = bge_name if bge_name != "VCHA\n(+PHC)" else "VCHA"
        bge_rm = rogers_row_map[bge_key]
        first_r = bge_rm["cell_plans"]
        last_r = bge_rm["total"]

        for label, rtype in NGTA_BGE_ROWS:
            r = bge_rm[rtype]
            set_row_props(ws, r, height=17, fmt=_frogb, opts=_collapsed)
            if r == first_r:
                write(ws, r, COL_A, a_label, _frogb)
                if a2_label:
                    write(ws, r + 1, COL_A, a2_label, _frogb)
            fmt_cell = _frogb_b if rtype == "total" else _frogb
            write(ws, r, COL_B, label, fmt_cell)
            if rtype == "total":
                write_monthly_sum_range(ws, r, first_r, last_r - 1, _frogb_b)
            else:
                for col in MONTH_COLS:
                    val = rogers_data.get((bge_key, rtype, col))
                    if val is not None:
                        write(ws, r, col, val, _frogb)

    # ---- aggregate TOTAL rows ----
    for r, label, rows_list in [
        (tot_plans, "TOTAL Cellular Plans", plans_rows),
        (tot_hw,    "TOTAL Cellular H/W",   hw_rows),
        (tot_dat,   "TOTAL Data",           dat_rows),
        (tot_voi,   "TOTAL Voice",          voi_rows),
        (tot_oth,   "TOTAL Other",          oth_rows),
    ]:
        set_row_props(ws, r, height=17, fmt=_frogh, opts=_collapsed)
        write(ws, r, COL_B, label, _frogh)
        write_monthly_sum_rows(ws, r, rows_list, _frogh)
        write(ws, r, COL_AN, label.replace("TOTAL ", ""))
        write_f(ws, r, COL_AR, q_sum(r, Y2025[0], Y2025[2]))
        write_f(ws, r, COL_AS, q_sum(r, Y2025[9], Y2025[11]))

    # ---- hidden sub-aggregate rows ----
    # Layout: sep + 5 data rows, repeated 4 times
    # (Gov & ECC, Health, Crown, School Districts).
    hidden_base = tot_oth + 1

    # Gov & ECC (formula: GovBC row + ECC row)
    gov_r = rogers_row_map["Gov BC"]
    ecc_r = rogers_row_map["ECC"]
    set_row_props(ws, hidden_base, height=16, fmt=_frogb, opts=_hidden)
    for idx, (label, rtype) in enumerate(_SPEND_TYPES):
        r = hidden_base + 1 + idx
        set_row_props(ws, r, height=17, fmt=_frogb, opts=_hidden)
        write(ws, r, COL_B, label, _frogb)
        write_monthly_formula(
            ws, r,
            lambda c, _rt=rtype: f"={col_letter(c)}{gov_r[_rt]}+{col_letter(c)}{ecc_r[_rt]}",
            _frogb,
        )
        write(ws, r, COL_AM, "Gov & ECC", _frogb)
        write(ws, r, COL_AN, label, _frogb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # Health (sum of health BGE rows)
    health_bges = ["FHA", "NHA", "ICBC", "PHSA", "IHA", "VIHA", "FNHA", "VCHA"]
    health_sep = hidden_base + 6
    set_row_props(ws, health_sep, height=16, fmt=_frogb, opts=_hidden)
    for idx, (label, rtype) in enumerate(_SPEND_TYPES):
        r = health_sep + 1 + idx
        set_row_props(ws, r, height=17, fmt=_frogb, opts=_hidden)
        write(ws, r, COL_B, label, _frogb)
        rows_list = [rogers_row_map[b][rtype] for b in health_bges]
        write_monthly_sum_rows(ws, r, rows_list, _frogb)
        write(ws, r, COL_AM, "Health", _frogb)
        write(ws, r, COL_AN, label, _frogb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # Crown Corps
    crown_bges = ["BCLC", "BC Hydro", "WSBC", "ICBC"]
    crown_sep = hidden_base + 12
    set_row_props(ws, crown_sep, height=16, fmt=_frogb, opts=_hidden)
    for idx, (label, rtype) in enumerate(_SPEND_TYPES):
        r = crown_sep + 1 + idx
        set_row_props(ws, r, height=17, fmt=_frogb, opts=_hidden)
        write(ws, r, COL_B, label, _frogb)
        rows_list = [rogers_row_map[b][rtype] for b in crown_bges]
        write_monthly_sum_rows(ws, r, rows_list, _frogb)
        write(ws, r, COL_AM, "Crown Corps", _frogb)
        write(ws, r, COL_AN, label, _frogb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # School Districts (reference to that single BGE's rows)
    sd_r = rogers_row_map["School Districts"]
    sd_sep = hidden_base + 18
    set_row_props(ws, sd_sep, height=16, fmt=_frogb, opts=_hidden)
    for idx, (label, rtype) in enumerate(_SPEND_TYPES):
        r = sd_sep + 1 + idx
        set_row_props(ws, r, height=17, fmt=_frogb, opts=_hidden)
        write(ws, r, COL_B, label, _frogb)
        write_monthly_ref(ws, r, sd_r[rtype], _frogb)
        write(ws, r, COL_AM, "School Districts", _frogb)
        write(ws, r, COL_AN, label, _frogb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # ---- optional cyan separator ----
    if include_separator:
        # Rogers keeps one blank row before the separator in the master sheet,
        # preserving the existing ROWS 232-354 layout.
        sep_r = hidden_base + 25
        set_row_props(ws, sep_r - 1, height=16)
        set_row_props(ws, sep_r, height=16, fmt=F(bg_color=BG_SEPARATOR))

    return sum_total_r
