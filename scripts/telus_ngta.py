"""TELUS NGTA section — report-view ingestion and worksheet section writer.

The section builder is parameterised by `first_row` so it can be embedded
inside the full spend_tracking workbook (first_row=110) or written as a
standalone file (first_row=5, after four rows of month/quarter headers).

Row layout, top to bottom (n = the 8 spend rows in NGTA_SPEND_ROWS)
---------------------------------
  TELUS NGTA header
  n summary rows, then the summary Total  <- returned by build_telus_ngta_section()
  BGEs header (outline level 1)
  14 BGEs x (n spend rows + Total)
  n aggregate TOTAL rows (outline level 1)
  hidden sub-totals: Gov & ECC, Health, Crown Corps, School Districts
    (a separator and n rows each)
  cyan separator (omitted when include_separator=False)
"""

import os
from datetime import datetime

from report_source import view_rows

from sheet_utils import (
    BG_TELUS_HDR, BG_TELUS_BGE, BG_SEPARATOR,
    COL_A, COL_B, COL_AM, COL_AN, COL_AO, COL_AP, COL_AR, COL_AS,
    MONTH_COLS, FIRST_MONTH, LAST_MONTH, Y2024, Y2025,
    BGES, BGE_A_LABELS, BGE_A2_LABELS, NGTA_SPEND_ROWS, NGTA_BGE_ROWS,
    _build_ngta_row_map, _ngta_rows_by_type,
    col_letter, annual_sum, q_sum, sum_rows,
    write, write_f, set_row_props,
    write_monthly_formula, write_monthly_ref,
    write_monthly_sum_rows, write_monthly_sum_range,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
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
    "BCA":  "Gov BC",   # combined with GBC under the same BGE row
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

# Maps report view columns → NGTA_BGE_ROWS row-type keys
SPEND_COL_MAP = {
    "cellular_plans":              "cell_plans",
    "cellular_hardware":           "cell_hw",
    "data_spend":                  "data",
    "voice_spend":                 "voice",
    "tls_spend":                   "tls",
    "professional_services_spend": "prof_services",
    "ancillary_hardware_spend":    "anc_hw",
    "other_spend":                 "other",
}

# ---------------------------------------------------------------------------
# Report view ingestion
# ---------------------------------------------------------------------------

# One row per TELUS tab and month (dbt view rpt_telus_ngta_monthly); entity_key is the tab.
TELUS_QUERY = """
    SELECT sheet_name AS entity_key, month_start,
           cellular_hardware, cellular_plans, data_spend, voice_spend,
           tls_spend, professional_services_spend, ancillary_hardware_spend, other_spend
    FROM intermediate.rpt_telus_ngta_monthly
"""

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


def load_telus_ngta() -> dict:
    """Read rpt_telus_ngta_monthly and return {(bge_key, row_type, col_idx): value}.

    Rows with unknown entity_key values or dates outside 2024-2026 are silently
    skipped.

    Values for the same (bge, row_type, col) are summed so multiple entity
    codes mapping to the same BGE (e.g., BCA + GBC → Gov BC) are combined
    into a single monthly figure.
    """
    data: dict = {}
    for row in view_rows(TELUS_QUERY):
        entity_raw = row.get("entity_key", "").strip().upper()
        bge = ENTITY_KEY_MAP.get(entity_raw)
        if bge is None:
            continue
        col = _month_to_col(row.get("month_start", ""))
        if col is None:
            continue
        for col_name, rtype in SPEND_COL_MAP.items():
            raw = row.get(col_name, "").strip()
            if not raw:
                continue
            try:
                val = float(raw.replace(",", ""))
            except ValueError:
                continue
            key = (bge, rtype, col)
            data[key] = data.get(key, 0.0) + val

    return data


# ---------------------------------------------------------------------------
# Section builder
# ---------------------------------------------------------------------------

def build_telus_ngta_section(ws, F, telus_data: dict, *,
                              first_row: int = 110,
                              include_separator: bool = True) -> tuple[int, int]:
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
        (summary Total row, next free row): the Total row for combined-total
        formulas, and the row the next section starts on.
    """
    # ---- derive all section-relative row positions ----
    n = len(NGTA_SPEND_ROWS)
    sum_start = first_row + 1            # n summary rows
    sum_total_r = sum_start + n          # summary Total
    bges_hdr = sum_total_r + 1
    bges_data_start = bges_hdr + 1
    telus_row_map, tot_start = _build_ngta_row_map(bges_data_start)

    _ftelh   = F.n(bg_color=BG_TELUS_HDR)
    _ftelh_b = F.n(bold=True, bg_color=BG_TELUS_HDR)
    _ftelb   = F.n(bg_color=BG_TELUS_BGE)
    _ftelb_b = F.n(bold=True, bg_color=BG_TELUS_BGE)
    _collapsed = {"level": 1, "hidden": True}
    _hidden  = {"hidden": True}

    # ---- section header ----
    set_row_props(ws, first_row, height=16, fmt=_ftelh)
    write(ws, first_row, COL_B, "TELUS NGTA", _ftelh_b)

    # ---- summary rows, one per spend row, each pointing at its TOTAL row ----
    for i, (label, _rtype) in enumerate(NGTA_SPEND_ROWS):
        r = sum_start + i
        set_row_props(ws, r, height=17, fmt=_ftelh)
        write(ws, r, COL_B, label, _ftelh)
        write_monthly_ref(ws, r, tot_start + i, _ftelh)
        write(ws, r, COL_AN, label)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # ---- summary Total row ----
    set_row_props(ws, sum_total_r, height=17, fmt=_ftelh, opts={"collapsed": True})
    write(ws, sum_total_r, COL_B, "Total", _ftelh_b)
    write_monthly_sum_range(ws, sum_total_r, sum_start, sum_start + n - 1, _ftelh_b)

    # ---- BGEs header ----
    set_row_props(ws, bges_hdr, fmt=_ftelh, opts=_collapsed)
    write(ws, bges_hdr, COL_A, "BGEs", _ftelh_b)

    # ---- BGE detail rows ----
    for bge_name, a_label, a2_label in zip(BGES, BGE_A_LABELS, BGE_A2_LABELS):
        bge_key = bge_name if bge_name != "VCHA\n(+PHC)" else "VCHA"
        bge_rm  = telus_row_map[bge_key]
        first_r = bge_rm["cell_plans"]
        last_r  = bge_rm["total"]

        for label, rtype in NGTA_BGE_ROWS:
            r = bge_rm[rtype]
            set_row_props(ws, r, height=17, fmt=_ftelb, opts=_collapsed)
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

    # ---- aggregate TOTAL rows, one per spend row ----
    for i, (label, rtype) in enumerate(NGTA_SPEND_ROWS):
        r = tot_start + i
        set_row_props(ws, r, height=17, fmt=_ftelh, opts=_collapsed)
        write(ws, r, COL_B, f"TOTAL {label}", _ftelh)
        write_monthly_sum_rows(ws, r, _ngta_rows_by_type(telus_row_map, rtype), _ftelh)
        write(ws, r, COL_AN, label)
        write_f(ws, r, COL_AR, q_sum(r, Y2025[0],  Y2025[2]))
        write_f(ws, r, COL_AS, q_sum(r, Y2025[9], Y2025[11]))

    # ---- hidden sub-aggregate rows ----
    # Layout: sep + n rows, repeated 4 times (Gov & ECC, Health, Crown, School Districts)
    _hidden_base = tot_start + n

    # Gov & ECC (formula: GovBC row + ECC row)
    gov_r = telus_row_map["Gov BC"]
    ecc_r = telus_row_map["ECC"]
    set_row_props(ws, _hidden_base, height=16, fmt=_ftelb, opts=_hidden)
    for idx, (label, rtype) in enumerate(NGTA_SPEND_ROWS):
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
    health_sep  = _hidden_base + (n + 1)
    set_row_props(ws, health_sep, height=16, fmt=_ftelb, opts=_hidden)
    for idx, (label, rtype) in enumerate(NGTA_SPEND_ROWS):
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
    crown_sep  = _hidden_base + 2 * (n + 1)
    set_row_props(ws, crown_sep, height=16, fmt=_ftelb, opts=_hidden)
    for idx, (label, rtype) in enumerate(NGTA_SPEND_ROWS):
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
    sd_sep = _hidden_base + 3 * (n + 1)
    set_row_props(ws, sd_sep, height=16, fmt=_ftelb, opts=_hidden)
    for idx, (label, rtype) in enumerate(NGTA_SPEND_ROWS):
        r = sd_sep + 1 + idx
        set_row_props(ws, r, height=17, fmt=_ftelb, opts=_hidden)
        write(ws, r, COL_B, label, _ftelb)
        write_monthly_ref(ws, r, sd_r[rtype], _ftelb)
        write(ws, r, COL_AM, "School Districts", _ftelb)
        write(ws, r, COL_AN, label, _ftelb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # ---- optional cyan separator ----
    next_row = _hidden_base + 4 * (n + 1)
    if include_separator:
        set_row_props(ws, next_row, height=16, fmt=F(bg_color=BG_SEPARATOR))
        next_row += 1

    return sum_total_r, next_row
