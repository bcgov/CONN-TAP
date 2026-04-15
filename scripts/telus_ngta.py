"""TELUS NGTA section — CSV ingestion and worksheet section writer.

The section builder is parameterised by `first_row` so it can be embedded
inside the full spend_tracking workbook (first_row=110) or written as a
standalone file (first_row=5, after four rows of month/quarter headers).

Row layout relative to first_row
---------------------------------
  first_row + 0     : TELUS NGTA header
  first_row + 1-5   : Summary rows (Cellular Plans / H/W / Data / Voice / Other)
  first_row + 6     : Summary Total  ← returned by build_telus_ngta_section()
  first_row + 7     : BGEs header (outline level 1)
  first_row + 8     : first BGE data row
  first_row + 91    : last BGE data row (14 BGEs × 6 rows)
  first_row + 92-96 : aggregate TOTAL rows (plans / hw / data / voice / other)
  first_row + 97    : hidden separator
  first_row + 98-102 : hidden Gov & ECC sub-totals
  first_row + 103   : hidden separator
  first_row + 104-108: hidden Health sub-totals
  first_row + 109   : hidden separator
  first_row + 110-114: hidden Crown Corps sub-totals
  first_row + 115   : hidden separator
  first_row + 116-120: hidden School Districts sub-totals
  first_row + 121   : cyan separator (omitted when include_separator=False)
"""

import csv
import os
from datetime import datetime

from sheet_utils import (
    BG_TELUS_HDR, BG_TELUS_BGE, BG_SEPARATOR,
    COL_A, COL_B, COL_AM, COL_AN, COL_AO, COL_AP, COL_AR, COL_AS,
    MONTH_COLS, FIRST_MONTH, LAST_MONTH, Y2024, Y2025,
    BGES, BGE_A_LABELS, BGE_A2_LABELS, NGTA_BGE_ROWS,
    _build_ngta_row_map, _ngta_rows_by_type,
    col_letter, annual_sum, q_sum, sum_rows,
    write, write_f, set_row_props,
    write_monthly_formula, write_monthly_ref,
    write_monthly_sum_rows, write_monthly_sum_range,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SOURCE_DIR  = os.path.join(os.path.dirname(__file__), "source")
TELUS_CSV   = os.path.join(SOURCE_DIR, "telus_ngta_spend.csv")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "telus_ngta_spend.xlsx")

# ---------------------------------------------------------------------------
# Entity-key mapping (case-insensitive, both short codes and full names)
# ---------------------------------------------------------------------------
ENTITY_KEY_MAP = {
    # Short codes
    "BCH":  "BC Hydro",
    "BCLC": "BCLC",
    "ECC":  "ECC",
    "MOE":  "ECC",
    "FHA":  "FHA",
    "FNHA": "FNHA",
    "GBC":  "Gov BC",
    "ICBC": "ICBC",
    "IHA":  "IHA",
    "NHA":  "NHA",
    "PHSA": "PHSA",
    "SD":   "School Districts",
    "VIHA": "VIHA",
    "VCHA": "VCHA",
    "WSBC": "WSBC",
    # Full-name variants
    "BC HYDRO":                             "BC Hydro",
    "FRASER HEALTH":                        "FHA",
    "FRASER HEALTH AUTHORITY":              "FHA",
    "FIRST NATIONS HEALTH AUTHORITY":       "FNHA",
    "GOVERNMENT OF BC":                     "Gov BC",
    "MINISTRY OF EDUCATION":                "ECC",
    "MINISTRY OF EDUCATION AND CHILD CARE": "ECC",
    "INTERIOR HEALTH":                      "IHA",
    "INTERIOR HEALTH AUTHORITY":            "IHA",
    "NORTHERN HEALTH":                      "NHA",
    "NORTHERN HEALTH AUTHORITY":            "NHA",
    "PROVINCIAL HEALTH SERVICES":           "PHSA",
    "PROVINCIAL HEALTH SERVICES AUTHORITY": "PHSA",
    "SCHOOL DISTRICTS":                     "School Districts",
    "SCHOOL DISTRICT":                      "School Districts",
    "VANCOUVER ISLAND HEALTH":              "VIHA",
    "VANCOUVER ISLAND HEALTH AUTHORITY":    "VIHA",
    "VANCOUVER COASTAL HEALTH":             "VCHA",
    "VANCOUVER COASTAL HEALTH AUTHORITY":   "VCHA",
    "WORKERS COMPENSATION BOARD":           "WSBC",
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

def _month_to_col(month_str: str):
    """Parse a month_start string → 0-based Excel column, or None if out of range."""
    s = month_str.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y/%m/%d", "%Y/%m", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(s, fmt)
            col = FIRST_MONTH + (dt.year - 2024) * 12 + (dt.month - 1)
            return col if FIRST_MONTH <= col <= LAST_MONTH else None
        except ValueError:
            continue
    return None


def load_telus_ngta(path: str = TELUS_CSV) -> dict:
    """Read telus_ngta_spend.csv and return {(bge_key, row_type, col_idx): value}.

    Rows with unknown entity_key values or dates outside 2024-2026 are silently
    skipped so the sheet still builds even with an incomplete CSV.
    """
    data: dict = {}
    if not os.path.exists(path):
        return data

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        reader.fieldnames = [h.strip().lower() for h in (reader.fieldnames or [])]
        for row in reader:
            entity_raw = row.get("entity_key", "").strip().upper()
            bge = ENTITY_KEY_MAP.get(entity_raw)
            if bge is None:
                continue
            col = _month_to_col(row.get("month_start", ""))
            if col is None:
                continue
            for csv_col, rtype in SPEND_COL_MAP.items():
                raw = row.get(csv_col, "").strip()
                if not raw:
                    continue
                try:
                    data[(bge, rtype, col)] = float(raw.replace(",", ""))
                except ValueError:
                    pass

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


def build_telus_ngta_section(ws, F, telus_data: dict, *,
                              first_row: int = 110,
                              include_separator: bool = True) -> int:
    """Write the complete TELUS NGTA section to *ws* starting at *first_row*.

    Args:
        ws:                xlsxwriter Worksheet.
        F:                 _FmtCache instance bound to the workbook.
        telus_data:        dict returned by load_telus_ngta().
        first_row:         Row number of the TELUS NGTA header (1-based).
                           Use 110 in the full spend_tracking sheet,
                           use 5 in the standalone telus_ngta_spend sheet.
        include_separator: Write the cyan separator row at the very end.

    Returns:
        The row number of the summary "Total" row so callers can reference
        it in combined-total formulas.
    """
    # ---- derive all section-relative row positions ----
    bges_data_start = first_row + 8
    telus_row_map, tot_start = _build_ngta_row_map(bges_data_start)
    # tot_start = first_row + 8 + 14×6 = first_row + 92

    tot_plans = tot_start
    tot_hw    = tot_start + 1
    tot_dat   = tot_start + 2
    tot_voi   = tot_start + 3
    tot_oth   = tot_start + 4

    plans_rows = _ngta_rows_by_type(telus_row_map, 'cell_plans')
    hw_rows    = _ngta_rows_by_type(telus_row_map, 'cell_hw')
    dat_rows   = _ngta_rows_by_type(telus_row_map, 'data')
    voi_rows   = _ngta_rows_by_type(telus_row_map, 'voice')
    oth_rows   = _ngta_rows_by_type(telus_row_map, 'other')

    _ftelh   = F(bg_color=BG_TELUS_HDR)
    _ftelh_b = F(bold=True, bg_color=BG_TELUS_HDR)
    _ftelb   = F(bg_color=BG_TELUS_BGE)
    _ftelb_b = F(bold=True, bg_color=BG_TELUS_BGE)
    _hidden  = {"hidden": True}

    # ---- section header ----
    set_row_props(ws, first_row, height=16, fmt=_ftelh)
    write(ws, first_row, COL_B, "TELUS NGTA", _ftelh_b)

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
        set_row_props(ws, r, height=17, fmt=_ftelh)
        write(ws, r, COL_B, label, _ftelh)
        write_monthly_ref(ws, r, tot_row, _ftelh)
        write(ws, r, COL_AN, label)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # ---- summary Total row ----
    sum_total_r = sum_start + 5   # = first_row + 6
    set_row_props(ws, sum_total_r, height=17, fmt=_ftelh)
    write(ws, sum_total_r, COL_B, "Total", _ftelh_b)
    write_monthly_sum_range(ws, sum_total_r, sum_start, sum_start + 4, _ftelh_b)

    # ---- BGEs header ----
    bges_hdr = first_row + 7
    set_row_props(ws, bges_hdr, fmt=_ftelh, opts={"level": 1})
    write(ws, bges_hdr, COL_A, "BGEs", _ftelh_b)

    # ---- BGE detail rows ----
    for bge_name, a_label, a2_label in zip(BGES, BGE_A_LABELS, BGE_A2_LABELS):
        bge_key = bge_name if bge_name != "VCHA\n(+PHC)" else "VCHA"
        bge_rm  = telus_row_map[bge_key]
        first_r = bge_rm["cell_plans"]
        last_r  = bge_rm["total"]

        for label, rtype in NGTA_BGE_ROWS:
            r = bge_rm[rtype]
            set_row_props(ws, r, height=17, fmt=_ftelb, opts={"level": 1})
            if r == first_r:
                write(ws, r, COL_A, a_label, _ftelb)
                if a2_label:
                    write(ws, r + 1, COL_A, a2_label, _ftelb)
            fmt_cell = _ftelb_b if rtype == "total" else _ftelb
            write(ws, r, COL_B, label, fmt_cell)
            if rtype == "total":
                write_monthly_sum_range(ws, r, first_r, last_r - 1, _ftelb_b)
            else:
                for col in MONTH_COLS:
                    val = telus_data.get((bge_key, rtype, col))
                    if val is not None:
                        write(ws, r, col, val, _ftelb)

    # ---- aggregate TOTAL rows ----
    for r, label, rows_list in [
        (tot_plans, "TOTAL Cellular Plans", plans_rows),
        (tot_hw,    "TOTAL Cellular H/W",   hw_rows),
        (tot_dat,   "TOTAL Data",            dat_rows),
        (tot_voi,   "TOTAL Voice",           voi_rows),
        (tot_oth,   "TOTAL Other",           oth_rows),
    ]:
        set_row_props(ws, r, height=17, fmt=_ftelh)
        write(ws, r, COL_B, label, _ftelh)
        write_monthly_sum_rows(ws, r, rows_list, _ftelh)
        write(ws, r, COL_AN, label.replace("TOTAL ", ""))
        write_f(ws, r, COL_AR, q_sum(r, Y2025[0],  Y2025[2]))
        write_f(ws, r, COL_AS, q_sum(r, Y2025[9], Y2025[11]))

    # ---- hidden sub-aggregate rows ----
    # Layout: sep + 5 data rows, repeated 4 times (Gov & ECC, Health, Crown, School Districts)
    _hidden_base = tot_oth + 1   # = first_row + 97

    # Gov & ECC (formula: GovBC row + ECC row)
    gov_r = telus_row_map["Gov BC"]
    ecc_r = telus_row_map["ECC"]
    set_row_props(ws, _hidden_base, height=16, fmt=_ftelb, opts=_hidden)
    for idx, (label, rtype) in enumerate(_SPEND_TYPES):
        r = _hidden_base + 1 + idx
        set_row_props(ws, r, height=17, fmt=_ftelb, opts=_hidden)
        write(ws, r, COL_B, label, _ftelb)
        write_monthly_formula(
            ws, r,
            lambda c, _rt=rtype: f"={col_letter(c)}{gov_r[_rt]}+{col_letter(c)}{ecc_r[_rt]}",
            _ftelb,
        )
        write(ws, r, COL_AM, "Gov & ECC", _ftelb)
        write(ws, r, COL_AN, label, _ftelb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # Health (sum of health BGE rows)
    health_bges = ["FHA", "NHA", "ICBC", "PHSA", "IHA", "VIHA", "FNHA", "VCHA"]
    health_sep  = _hidden_base + 6
    set_row_props(ws, health_sep, height=16, fmt=_ftelb, opts=_hidden)
    for idx, (label, rtype) in enumerate(_SPEND_TYPES):
        r = health_sep + 1 + idx
        set_row_props(ws, r, height=17, fmt=_ftelb, opts=_hidden)
        write(ws, r, COL_B, label, _ftelb)
        rows_list = [telus_row_map[b][rtype] for b in health_bges]
        write_monthly_sum_rows(ws, r, rows_list, _ftelb)
        write(ws, r, COL_AM, "Health", _ftelb)
        write(ws, r, COL_AN, label, _ftelb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # Crown Corps
    crown_bges = ["BCLC", "BC Hydro", "WSBC", "ICBC"]
    crown_sep  = _hidden_base + 12
    set_row_props(ws, crown_sep, height=16, fmt=_ftelb, opts=_hidden)
    for idx, (label, rtype) in enumerate(_SPEND_TYPES):
        r = crown_sep + 1 + idx
        set_row_props(ws, r, height=17, fmt=_ftelb, opts=_hidden)
        write(ws, r, COL_B, label, _ftelb)
        rows_list = [telus_row_map[b][rtype] for b in crown_bges]
        write_monthly_sum_rows(ws, r, rows_list, _ftelb)
        write(ws, r, COL_AM, "Crown Corps", _ftelb)
        write(ws, r, COL_AN, label, _ftelb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # School Districts (reference to that single BGE's rows)
    sd_r   = telus_row_map["School Districts"]
    sd_sep = _hidden_base + 18
    set_row_props(ws, sd_sep, height=16, fmt=_ftelb, opts=_hidden)
    for idx, (label, rtype) in enumerate(_SPEND_TYPES):
        r = sd_sep + 1 + idx
        set_row_props(ws, r, height=17, fmt=_ftelb, opts=_hidden)
        write(ws, r, COL_B, label, _ftelb)
        write_monthly_ref(ws, r, sd_r[rtype], _ftelb)
        write(ws, r, COL_AM, "School Districts", _ftelb)
        write(ws, r, COL_AN, label, _ftelb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # ---- optional cyan separator ----
    if include_separator:
        sep_r = _hidden_base + 24   # = first_row + 121
        set_row_props(ws, sep_r, height=16, fmt=F(bg_color=BG_SEPARATOR))

    return sum_total_r
