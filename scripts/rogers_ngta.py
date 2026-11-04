"""Rogers NGTA section - report-view ingestion and worksheet section writer.

The section builder is parameterised by `first_row` so it can be embedded
inside the full spend_tracking workbook (first_row=232) or written as a
standalone file (first_row=5, after four rows of month/quarter headers).

Row layout, top to bottom (n = the 7 spend rows in ROGERS_SPEND_ROWS)
---------------------------------
  Rogers NGTA header
  n summary rows, then the summary Total  <- returned by build_rogers_ngta_section()
  BGEs header (outline level 1)
  14 BGEs x (n spend rows + Total)
  n aggregate TOTAL rows (outline level 1)
  hidden sub-totals: Gov & ECC, Health, Crown Corps, School Districts
    (a separator and n rows each)
  blank row + cyan separator (omitted when include_separator=False)
"""

import os
from datetime import datetime

from report_source import view_rows

from sheet_utils import (
    BG_ROGERS_HDR, BG_ROGERS_BGE, BG_SEPARATOR,
    COL_A, COL_B, COL_AM, COL_AN, COL_AO, COL_AP, COL_AR, COL_AS,
    MONTH_COLS, FIRST_MONTH, LAST_MONTH, Y2024, Y2025,
    BGES, BGE_A_LABELS, BGE_A2_LABELS, ROGERS_SPEND_ROWS, ROGERS_BGE_ROWS,
    _build_ngta_row_map, _ngta_rows_by_type,
    col_letter, annual_sum, q_sum,
    write, write_f, set_row_props,
    write_monthly_formula, write_monthly_ref,
    write_monthly_sum_rows, write_monthly_sum_range,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "rogers_ngta_spend.xlsx")

# ---------------------------------------------------------------------------
# BGE code -> workbook row
# ---------------------------------------------------------------------------
# The dbt view rpt_rogers_ngta_monthly has already resolved every
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

# Maps report view columns → ROGERS_BGE_ROWS row-type keys
SPEND_COL_MAP = {
    "cellular_plans":              "cell_plans",
    "cellular_hardware":           "cell_hw",
    "data_spend":                  "data",
    "voice_spend":                 "voice",
    "professional_services_spend": "prof_services",
    "ancillary_hardware_spend":    "anc_hw",
    "other_spend":                 "other",
}

# ---------------------------------------------------------------------------
# Report view ingestion
# ---------------------------------------------------------------------------

# One row per BGE and month (dbt view rpt_rogers_ngta_monthly); entity_key is the BGE code.
ROGERS_QUERY = """
    SELECT entity_key, month_start, cellular_hardware, cellular_plans,
           data_spend, voice_spend, professional_services_spend,
           ancillary_hardware_spend, other_spend, total_reported
    FROM intermediate.rpt_rogers_ngta_monthly
"""


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


def load_rogers_ngta() -> dict[tuple[str, str, int], float]:
    """Read rpt_rogers_ngta_monthly and return {(bge_key, row_type, col_idx): value}.

    One row per BGE and month. Months outside 2024-2026 are skipped. A BGE code
    with no workbook row is skipped too, but listed on stdout so it can't go missing
    unnoticed. Values for the same (bge, row_type, col) are summed.
    """
    data: dict[tuple[str, str, int], float] = {}
    skipped: dict[str, float] = {}
    for row in view_rows(ROGERS_QUERY):
        col = _month_to_col(_first_value(row, "month_start", "month"))
        if col is None:
            continue
        bge = _resolve_bge(row)
        if not bge:
            key = row.get("entity_key") or "<blank>"
            skipped[key] = skipped.get(key, 0.0) + (_amount(row.get("total_reported", "")) or 0.0)
            continue
        for col_name, row_type in SPEND_COL_MAP.items():
            _add(data, bge, row_type, col, _amount(row.get(col_name, "")))
    for key, total in sorted(skipped.items()):
        print(f"  ! Rogers: no workbook row for BGE {key!r}; skipped {total:,.2f}")
    return data


# ---------------------------------------------------------------------------
# Section builder
# ---------------------------------------------------------------------------

def build_rogers_ngta_section(ws, F, rogers_data: dict, *,
                               first_row: int = 232,
                               include_separator: bool = True) -> tuple[int, int]:
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
        (summary Total row, next free row): the Total row for combined-total
        formulas, and the row the next section starts on.
    """
    # ---- derive all section-relative row positions ----
    n = len(ROGERS_SPEND_ROWS)
    sum_start = first_row + 1            # n summary rows
    sum_total_r = sum_start + n          # summary Total
    bges_hdr = sum_total_r + 1
    bges_data_start = bges_hdr + 1
    rogers_row_map, tot_start = _build_ngta_row_map(bges_data_start, ROGERS_BGE_ROWS)

    _frogh   = F.n(bg_color=BG_ROGERS_HDR)
    _frogh_b = F.n(bold=True, bg_color=BG_ROGERS_HDR)
    _frogb   = F.n(bg_color=BG_ROGERS_BGE)
    _frogb_b = F.n(bold=True, bg_color=BG_ROGERS_BGE)
    _collapsed = {"level": 1, "hidden": True}
    _hidden  = {"hidden": True}

    # ---- section header ----
    set_row_props(ws, first_row, height=16, fmt=_frogh)
    write(ws, first_row, COL_B, "Rogers NGTA", _frogh_b)

    # ---- summary rows, one per spend row, each pointing at its TOTAL row ----
    for i, (label, _rtype) in enumerate(ROGERS_SPEND_ROWS):
        r = sum_start + i
        set_row_props(ws, r, height=17, fmt=_frogh)
        write(ws, r, COL_B, label, _frogh)
        write_monthly_ref(ws, r, tot_start + i, _frogh)
        write(ws, r, COL_AN, label)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # ---- summary Total row ----
    set_row_props(ws, sum_total_r, height=17, fmt=_frogh, opts={"collapsed": True})
    write(ws, sum_total_r, COL_B, "Total", _frogh_b)
    write_monthly_sum_range(ws, sum_total_r, sum_start, sum_start + n - 1, _frogh_b)

    # ---- BGEs header ----
    set_row_props(ws, bges_hdr, fmt=_frogh, opts=_collapsed)
    write(ws, bges_hdr, COL_A, "BGEs", _frogh_b)

    # ---- BGE detail rows ----
    for bge_name, a_label, a2_label in zip(BGES, BGE_A_LABELS, BGE_A2_LABELS):
        bge_key = bge_name if bge_name != "VCHA\n(+PHC)" else "VCHA"
        bge_rm = rogers_row_map[bge_key]
        first_r = bge_rm["cell_plans"]
        last_r = bge_rm["total"]

        for label, rtype in ROGERS_BGE_ROWS:
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

    # ---- aggregate TOTAL rows, one per spend row ----
    for i, (label, rtype) in enumerate(ROGERS_SPEND_ROWS):
        r = tot_start + i
        set_row_props(ws, r, height=17, fmt=_frogh, opts=_collapsed)
        write(ws, r, COL_B, f"TOTAL {label}", _frogh)
        write_monthly_sum_rows(ws, r, _ngta_rows_by_type(rogers_row_map, rtype), _frogh)
        write(ws, r, COL_AN, label)
        write_f(ws, r, COL_AR, q_sum(r, Y2025[0], Y2025[2]))
        write_f(ws, r, COL_AS, q_sum(r, Y2025[9], Y2025[11]))

    # ---- hidden sub-aggregate rows ----
    # Layout: sep + n rows, repeated 4 times
    # (Gov & ECC, Health, Crown, School Districts).
    hidden_base = tot_start + n

    # Gov & ECC (formula: GovBC row + ECC row)
    gov_r = rogers_row_map["Gov BC"]
    ecc_r = rogers_row_map["ECC"]
    set_row_props(ws, hidden_base, height=16, fmt=_frogb, opts=_hidden)
    for idx, (label, rtype) in enumerate(ROGERS_SPEND_ROWS):
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
    health_sep = hidden_base + (n + 1)
    set_row_props(ws, health_sep, height=16, fmt=_frogb, opts=_hidden)
    for idx, (label, rtype) in enumerate(ROGERS_SPEND_ROWS):
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
    crown_sep = hidden_base + 2 * (n + 1)
    set_row_props(ws, crown_sep, height=16, fmt=_frogb, opts=_hidden)
    for idx, (label, rtype) in enumerate(ROGERS_SPEND_ROWS):
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
    sd_sep = hidden_base + 3 * (n + 1)
    set_row_props(ws, sd_sep, height=16, fmt=_frogb, opts=_hidden)
    for idx, (label, rtype) in enumerate(ROGERS_SPEND_ROWS):
        r = sd_sep + 1 + idx
        set_row_props(ws, r, height=17, fmt=_frogb, opts=_hidden)
        write(ws, r, COL_B, label, _frogb)
        write_monthly_ref(ws, r, sd_r[rtype], _frogb)
        write(ws, r, COL_AM, "School Districts", _frogb)
        write(ws, r, COL_AN, label, _frogb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # ---- optional cyan separator ----
    next_row = hidden_base + 4 * (n + 1)
    if include_separator:
        # Rogers keeps one blank row before the separator in the master sheet.
        set_row_props(ws, next_row, height=16)
        set_row_props(ws, next_row + 1, height=16, fmt=F(bg_color=BG_SEPARATOR))
        next_row += 2

    return sum_total_r, next_row
