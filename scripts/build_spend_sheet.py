#!/usr/bin/env python3
"""
Recreate the spend tracking spreadsheet using xlsxwriter.

Organized into 6 fillable categories:
  1. tsma           – TSMA BGE detail (rows 11-90)
  2. mms            – MMS summary row and within-BGE MMS sub-rows
  3. telus_ngta     – TELUS NGTA BGE detail (rows 116-190)
  4. rogers_ngta    – Rogers NGTA BGE detail (rows 218-292)
  5. out_of_scope   – Out-of-Scope sub-categories (rows 315-344)
  6. tsma_lite      – TSMA Lite quarterly data (rows 346-354)

Run:  python3 scripts/build_spend_sheet.py
Output: scripts/spend_tracking.xlsx
"""

import os
import xlsxwriter

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "spend_tracking.xlsx")


# ---------------------------------------------------------------------------
# Theme color resolution
# ---------------------------------------------------------------------------
# Base hex colors from xl/theme/theme1.xml (no leading #)
_THEME_BASE = {
    3: "0E2841",   # dk2  – dark navy (OOXML fill theme=3 → Text 2)
    5: "E97132",   # accent2 – orange
    6: "196B24",   # accent3 – dark green
    8: "A02B93",   # accent5 – purple/magenta
}


def _tint(hex6: str, tint: float) -> str:
    """Apply Excel tint to a 6-char hex color string and return #RRGGBB."""
    r, g, b = int(hex6[0:2], 16), int(hex6[2:4], 16), int(hex6[4:6], 16)
    if tint >= 0:
        r2 = r + (255 - r) * tint
        g2 = g + (255 - g) * tint
        b2 = b + (255 - b) * tint
    else:
        r2, g2, b2 = r * (1 + tint), g * (1 + tint), b * (1 + tint)
    return "#{:02X}{:02X}{:02X}".format(
        max(0, min(255, round(r2))),
        max(0, min(255, round(g2))),
        max(0, min(255, round(b2))),
    )


# Pre-resolved fill colors
BG_TSMA_HDR  = _tint(_THEME_BASE[3], 0.750)   # #C3C9D0  – TSMA header/summary/totals
BG_TSMA_BGE  = _tint(_THEME_BASE[3], 0.900)   # #E7EAEC  – TSMA BGE detail rows
BG_COMBINED  = _tint(_THEME_BASE[6], 0.600)   # #A3C4A7  – row 91 combined total
BG_SEPARATOR = "#00B0F0"                        # bright cyan – separator rows
BG_TELUS_HDR = _tint(_THEME_BASE[8], 0.600)   # #D9AAD4  – TELUS header/summary/totals
BG_TELUS_BGE = _tint(_THEME_BASE[8], 0.800)   # #ECD5E9  – TELUS BGE detail rows
BG_ROGERS_HDR = _tint(_THEME_BASE[5], 0.600)  # #F6C6AD  – Rogers header/summary/totals
BG_ROGERS_BGE = _tint(_THEME_BASE[5], 0.800)  # #FBE3D6  – Rogers BGE detail rows
BG_IVR        = "#FFA7A7"                       # light red – Voice-IVR rows


class _FmtCache:
    """On-demand xlsxwriter format factory – reuses identical format objects."""
    def __init__(self, wb):
        self._wb = wb
        self._cache = {}

    def __call__(self, **props):
        key = tuple(sorted(props.items()))
        if key not in self._cache:
            self._cache[key] = self._wb.add_format(props)
        return self._cache[key]

# ---------------------------------------------------------------------------
# Column index helpers (0-based)
# ---------------------------------------------------------------------------

def col_letter(col_idx: int) -> str:
    """Convert 0-based column index to Excel letter(s)."""
    col = col_idx + 1
    result = ""
    while col:
        col, rem = divmod(col - 1, 26)
        result = chr(65 + rem) + result
    return result


def cr(row_1: int, col_0: int) -> str:
    """Cell reference from 1-based row and 0-based column."""
    return f"{col_letter(col_0)}{row_1}"


# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

COL_A = 0     # entity name
COL_B = 1     # sub-label  (width 43)
# Months: C (col 2) = Jan 2024 … AL (col 37) = Dec 2026  →  36 months
FIRST_MONTH = 2
LAST_MONTH  = 37
MONTH_COLS  = list(range(FIRST_MONTH, LAST_MONTH + 1))

# 2024 = C:N (cols 2-13), 2025 = O:Z (14-25), 2026 = AA:AL (26-37)
Y2024 = list(range(2, 14))
Y2025 = list(range(14, 26))
Y2026 = list(range(26, 38))

# Summary / analysis columns (0-based)
COL_AM = 38   # group label (visible)
COL_AN = 39   # row label   (hidden)
COL_AO = 40   # 2024 annual (hidden)
COL_AP = 41   # 2025 annual (hidden)
COL_AQ = 42   # Q1 2024    (visible)
COL_AR = 43   # Q1 2025    (hidden)
COL_AS = 44   # Q4 2025    (hidden)

# Quarter-end columns used by TSMA Lite (end-of-each-quarter month)
# E=4,H=7,K=10,N=13  Q=16,T=19,W=22,Z=25  AC=28,AF=31,AI=34,AL=37
TSMA_LITE_Q_COLS = [4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34, 37]

# Month labels (Jan 2024 … Dec 2026)
_MNAMES = ['Jan','Feb','Mar','Apr','May','Jun',
           'Jul','Aug','Sep','Oct','Nov','Dec']
MONTH_LABELS: list[str] = []
for _yr in [2024, 2025, 2026]:
    for _mi, _mn in enumerate(_MNAMES):
        # Original uses 'Sept' for Sep-2024 only
        label = f"{'Sept' if (_yr == 2024 and _mi == 8) else _mn} {_yr}"
        MONTH_LABELS.append(label)

# BGE entities shared by all three carrier sections
BGES = [
    "Gov BC",
    "BCLC",
    "BC Hydro",
    "WSBC",
    "ECC",
    "FHA",
    "NHA",
    "ICBC",
    "PHSA",
    "IHA",
    "VIHA",
    "FNHA",
    "VCHA\n(+PHC)",   # A-column label uses two lines
    "School Districts",
]
BGE_A_LABELS = [
    "Gov BC", "BCLC", "BC Hydro", "WSBC", "ECC",
    "FHA", "NHA", "ICBC", "PHSA", "IHA",
    "VIHA", "FNHA", "VCHA", "School Districts",
]
BGE_A2_LABELS = [
    None, None, None, None, None,
    None, None, None, None, None,
    None, None, "(+PHC)", None,
]

# ---------------------------------------------------------------------------
# TSMA BGE sub-row definitions
# Each tuple: (B-label, row-type)
# row-type: 'cellular'|'data'|'voice'|'voice_ivr'|'oos'|'mms'|'total'
# ---------------------------------------------------------------------------
TSMA_BGE_ROWS = {
    "Gov BC":          [('Cellular','cellular'),('Data','data'),('Voice','voice'),
                        ('Voice - IVR','voice_ivr'),('Out of Scope','oos'),('Total','total')],
    "BCLC":            [('Cellular','cellular'),('Data','data'),('Voice','voice'),
                        ('Out of Scope','oos'),('Total','total')],
    "BC Hydro":        [('Cellular','cellular'),('Data','data'),('Voice','voice'),
                        ('Out of Scope','oos'),('Total','total')],
    "WSBC":            [('Cellular','cellular'),('Data','data'),('Voice','voice'),
                        ('Out of Scope','oos'),('Total','total')],
    "ECC":             [('Cellular','cellular'),('Data','data'),('Voice','voice'),
                        ('Out of Scope','oos'),('Total','total')],
    "FHA":             [('Cellular','cellular'),('MMS','mms'),('Data','data'),('Voice','voice'),
                        ('Out of Scope','oos'),('Total','total')],
    "NHA":             [('Cellular','cellular'),('Data','data'),('Voice','voice'),
                        ('Out of Scope','oos'),('Total','total')],
    "ICBC":            [('Cellular','cellular'),('Data','data'),('Voice','voice'),
                        ('Out of Scope','oos'),('Total','total')],
    "PHSA":            [('Cellular','cellular'),('MMS','mms'),('Data','data'),('Voice','voice'),
                        ('Out of Scope MWLAN)','oos'),('Total','total')],
    "IHA":             [('Cellular','cellular'),('Data','data'),('Voice','voice'),
                        ('Out of Scope','oos'),('Total','total')],
    "VIHA":            [('Cellular','cellular'),('Data','data'),('Voice','voice'),
                        ('Out of Scope','oos'),('Total','total')],
    "FNHA":            [('Cellular','cellular'),('Data','data'),('Voice','voice'),
                        ('Out of Scope','oos'),('Total','total')],
    "VCHA":            [('Cellular','cellular'),('MMS','mms'),('Data','data'),('Voice','voice'),
                        ('Out of Scope MWLAN)','oos'),('Total','total')],
    "School Districts":[('Cellular','cellular'),('Data','data'),('Voice','voice'),
                        ('Out of Scope','oos'),('Total','total')],
}

# TELUS / Rogers NGTAs have the same sub-row structure per BGE
NGTA_BGE_ROWS = [
    ('Cellular Plans', 'cell_plans'),
    ('Cellular H/W',   'cell_hw'),
    ('Data',           'data'),
    ('Voice',          'voice'),
    ('Total',          'total'),
]

# ---------------------------------------------------------------------------
# Pre-compute TSMA row numbers (1-based)
# ---------------------------------------------------------------------------

def _build_tsma_row_map():
    """Return {bge_name: {row_type: excel_row_number}} and aggregate row numbers."""
    row_map = {}
    r = 12  # first BGE data row
    for bge in BGE_A_LABELS:
        rows_for_bge = TSMA_BGE_ROWS[bge]
        row_map[bge] = {}
        for label, rtype in rows_for_bge:
            row_map[bge][rtype] = r
            r += 1
    # r is now 86 (TOTAL rows)
    assert r == 86, f"Expected TSMA TOTAL at row 86, got {r}"
    return row_map, r  # r=86 = first TOTAL row


TSMA_ROW_MAP, _TSMA_TOTAL_START = _build_tsma_row_map()

# TSMA aggregate rows (1-based)
ROW_TSMA_TOTAL_CEL = 86
ROW_TSMA_TOTAL_MMS = 87
ROW_TSMA_TOTAL_DAT = 88
ROW_TSMA_TOTAL_VOI = 89
ROW_TSMA_TOTAL_OOS = 90

# TSMA summary rows (1-based)
ROW_TSMA_SUM_CEL = 5
ROW_TSMA_SUM_DAT = 6
ROW_TSMA_SUM_VOI = 7
ROW_TSMA_SUM_OOS = 8
ROW_TSMA_SUM_TOT = 9
ROW_TSMA_SUM_MMS = 10

# ---------------------------------------------------------------------------
# Pre-compute TELUS NGTA row numbers
# ---------------------------------------------------------------------------

def _build_ngta_row_map(start_row: int):
    """Return {bge_name: {row_type: row_number}} with 5 rows per BGE."""
    row_map = {}
    r = start_row
    for bge in BGE_A_LABELS:
        row_map[bge] = {}
        for label, rtype in NGTA_BGE_ROWS:
            row_map[bge][rtype] = r
            r += 1
    return row_map, r   # r = first TOTAL row


# TELUS NGTA  – BGEs start at row 117, summary at 111-115
ROW_TELUS_BGES_START = 117
TELUS_ROW_MAP, _TELUS_TOTAL_START = _build_ngta_row_map(ROW_TELUS_BGES_START)
assert _TELUS_TOTAL_START == 187

ROW_TELUS_TOT_PLANS = 187
ROW_TELUS_TOT_HW    = 188
ROW_TELUS_TOT_DAT   = 189
ROW_TELUS_TOT_VOI   = 190

# Rogers NGTA – BGEs start at row 219, summary at 213-217
ROW_ROGERS_BGES_START = 219
ROGERS_ROW_MAP, _ROGERS_TOTAL_START = _build_ngta_row_map(ROW_ROGERS_BGES_START)
assert _ROGERS_TOTAL_START == 289

ROW_ROGERS_TOT_PLANS = 289
ROW_ROGERS_TOT_HW    = 290
ROW_ROGERS_TOT_DAT   = 291
ROW_ROGERS_TOT_VOI   = 292

# ---------------------------------------------------------------------------
# Collect row lists needed for aggregate formulas
# ---------------------------------------------------------------------------

def _tsma_rows_by_type(rtype):
    return [TSMA_ROW_MAP[b][rtype] for b in BGE_A_LABELS if rtype in TSMA_ROW_MAP[b]]


def _ngta_rows_by_type(row_map, rtype):
    return [row_map[b][rtype] for b in BGE_A_LABELS if rtype in row_map[b]]


# TSMA aggregate formulas reference specific rows (matching original exactly)
# TOTAL Cellular includes School Districts Cellular AND Data rows
TSMA_CEL_ROWS = (_tsma_rows_by_type('cellular')
                 + [TSMA_ROW_MAP['School Districts']['data']])
TSMA_MMS_ROWS = _tsma_rows_by_type('mms')
TSMA_DAT_ROWS = _tsma_rows_by_type('data')
TSMA_VOI_ROWS = _tsma_rows_by_type('voice') + _tsma_rows_by_type('voice_ivr')
TSMA_OOS_ROWS = _tsma_rows_by_type('oos')

TELUS_PLANS_ROWS = _ngta_rows_by_type(TELUS_ROW_MAP, 'cell_plans')
TELUS_HW_ROWS    = _ngta_rows_by_type(TELUS_ROW_MAP, 'cell_hw')
TELUS_DAT_ROWS   = _ngta_rows_by_type(TELUS_ROW_MAP, 'data')
TELUS_VOI_ROWS   = _ngta_rows_by_type(TELUS_ROW_MAP, 'voice')

ROGERS_PLANS_ROWS = _ngta_rows_by_type(ROGERS_ROW_MAP, 'cell_plans')
ROGERS_HW_ROWS    = _ngta_rows_by_type(ROGERS_ROW_MAP, 'cell_hw')
ROGERS_DAT_ROWS   = _ngta_rows_by_type(ROGERS_ROW_MAP, 'data')
ROGERS_VOI_ROWS   = _ngta_rows_by_type(ROGERS_ROW_MAP, 'voice')

# Out of Scope rows (1-based, level-1 detail rows)
OOS_MANAGED_ROUTER_ROWS = list(range(317, 324))   # 317-323
OOS_MANAGED_WLAN_ROWS   = list(range(326, 332))   # 326-331
OOS_MANAGED_SEC_ROWS    = list(range(334, 344))   # 334-343

# TSMA Lite (1-based)
ROW_TSMALITE_VOICE  = 347
ROW_TSMALITE_DATA   = 348
ROW_TSMALITE_OTHER  = 349
ROW_TSMALITE_CELUE  = 350
ROW_TSMALITE_TOTAL  = 351   # SUM of 347:350 in Q-end columns
ROW_TSMALITE_EXC    = 353   # Voice+Data+Other (excludes cellular UE)
ROW_TSMALITE_CELUE2 = 354   # = cellular UE reference


# ---------------------------------------------------------------------------
# Formula builders
# ---------------------------------------------------------------------------

def sum_rows(rows: list[int], col: int) -> str:
    """=rowA + rowB + … for a given column."""
    cl = col_letter(col)
    return "=" + "+".join(f"{cl}{r}" for r in rows)


def sum_range(r1: int, r2: int, col: int) -> str:
    cl = col_letter(col)
    return f"=SUM({cl}{r1}:{cl}{r2})"


def ref_cell(target_row: int, col: int) -> str:
    return f"={col_letter(col)}{target_row}"


def annual_sum(row: int, year_cols: list[int]) -> str:
    cl_start = col_letter(year_cols[0])
    cl_end   = col_letter(year_cols[-1])
    return f"=SUM({cl_start}{row}:{cl_end}{row})"


def q_sum(row: int, q_start_col: int, q_end_col: int) -> str:
    return f"=SUM({col_letter(q_start_col)}{row}:{col_letter(q_end_col)}{row})"


# ---------------------------------------------------------------------------
# Sheet-writing helpers
# ---------------------------------------------------------------------------

def write(ws, row_1: int, col_0: int, val, fmt=None):
    args = (row_1 - 1, col_0, val)
    ws.write(*args, fmt) if fmt else ws.write(*args)


def write_f(ws, row_1: int, col_0: int, formula: str, fmt=None):
    args = (row_1 - 1, col_0, formula)
    ws.write_formula(*args, fmt) if fmt else ws.write_formula(*args)


def merge(ws, r1: int, c1: int, r2: int, c2: int, val, fmt=None):
    args = (r1 - 1, c1, r2 - 1, c2, val)
    ws.merge_range(*args, fmt) if fmt else ws.merge_range(*args)


def set_row_props(ws, row_1: int, height=None, fmt=None, opts=None):
    ws.set_row(row_1 - 1, height, fmt, opts or {})


def write_monthly_formula(ws, row_1: int, formula_fn, fmt=None):
    """Write formula_fn(col) for every month column."""
    for col in MONTH_COLS:
        write_f(ws, row_1, col, formula_fn(col), fmt)


def write_monthly_ref(ws, row_1: int, target_row: int, fmt=None):
    write_monthly_formula(ws, row_1, lambda c: ref_cell(target_row, c), fmt)


def write_monthly_sum_rows(ws, row_1: int, rows: list[int], fmt=None):
    write_monthly_formula(ws, row_1, lambda c: sum_rows(rows, c), fmt)


def write_monthly_sum_range(ws, row_1: int, r_start: int, r_end: int, fmt=None):
    write_monthly_formula(ws, row_1, lambda c: sum_range(r_start, r_end, c), fmt)


def write_summary_cols(ws, row_1: int, label: str,
                       include_annual=True, include_q=True):
    """Write the hidden summary/analysis columns AN-AS for a row."""
    write(ws, row_1, COL_AN, label)
    if include_annual:
        write_f(ws, row_1, COL_AO, annual_sum(row_1, Y2024))
        write_f(ws, row_1, COL_AP, annual_sum(row_1, Y2025))
    if include_q:
        write_f(ws, row_1, COL_AQ, q_sum(row_1, Y2024[0], Y2024[2]))   # Q1 2024
        write_f(ws, row_1, COL_AR, q_sum(row_1, Y2025[0], Y2025[2]))   # Q1 2025
        write_f(ws, row_1, COL_AS, q_sum(row_1, Y2025[9], Y2025[11]))  # Q4 2025


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build():
    wb = xlsxwriter.Workbook(OUTPUT_PATH)
    ws = wb.add_worksheet("Sheet1")

    # Outline: summary rows BELOW detail, collapse buttons on right
    ws.outline_settings(True, False, True, True)

    # --- Format factory ---
    F = _FmtCache(wb)

    # Convenience aliases (no background – for header rows that have no fill)
    f_bold    = F(bold=True)
    f_normal  = F()
    f_total   = F(bold=True)
    f_section = F(bold=True)

    # --- Column widths ---
    ws.set_column(COL_A, COL_A, 10.5)
    ws.set_column(COL_B, COL_B, 43.0)
    ws.set_column(FIRST_MONTH, LAST_MONTH, 10.5)
    # Individual overrides matching original
    ws.set_column(11, 11, 11.5)   # L
    ws.set_column(18, 18, 11.17)  # S
    ws.set_column(26, 26, 10.83)  # AA
    ws.set_column(28, 28, 8.83)   # AC
    ws.set_column(29, 29, 8.5)    # AD
    ws.set_column(30, 30, 9.0)    # AE
    ws.set_column(31, 31, 8.5)    # AF
    ws.set_column(32, 32, 7.83)   # AG
    ws.set_column(33, 33, 8.66)   # AH
    ws.set_column(34, 34, 8.5)    # AI
    ws.set_column(COL_AM, COL_AM, 13.5)
    ws.set_column(COL_AN, COL_AN, 13.5, None, {"hidden": True})
    ws.set_column(COL_AO, COL_AO, 13.33, None, {"hidden": True})
    ws.set_column(COL_AP, COL_AP, 12.0,  None, {"hidden": True})
    ws.set_column(COL_AQ, COL_AQ, 11.5)
    ws.set_column(COL_AR, COL_AR, 11.5,  None, {"hidden": True})
    ws.set_column(COL_AS, COL_AS, 9.83,  None, {"hidden": True})

    # =========================================================
    # ROWS 1-3: Year / Quarter headers
    # =========================================================
    set_row_props(ws, 3, height=16)

    # Row 1 – Year spans
    merge(ws, 1, 2,  1, 13, 2024, f_bold)
    merge(ws, 1, 14, 1, 25, 2025, f_bold)
    merge(ws, 1, 26, 1, 37, 2026, f_bold)

    # Row 2 – Calendar quarters (CQ) + summary col headers
    cq = ["CQ1", "CQ2", "CQ3", "CQ4"]
    for yr_start in [2, 14, 26]:
        for qi, label in enumerate(cq):
            c = yr_start + qi * 3
            merge(ws, 2, c, 2, c + 2, label, f_bold)
    write(ws, 2, COL_AO, 2024,       f_bold)
    write(ws, 2, COL_AP, 2025,       f_bold)
    write(ws, 2, COL_AQ, "Q1 2024",  f_bold)
    write(ws, 2, COL_AR, "Q1 2025",  f_bold)
    write(ws, 2, COL_AS, "Q4 2025",  f_bold)

    # Row 3 – Fiscal quarters (FQ) + Jan-Dec label
    fq = ["FQ4", "FQ1", "FQ2", "FQ3"]
    for yr_start in [2, 14, 26]:
        for qi, label in enumerate(fq):
            c = yr_start + qi * 3
            merge(ws, 3, c, 3, c + 2, label, f_bold)
    write(ws, 3, COL_AO, "Jan-Dec")

    # =========================================================
    # ROW 4: Month labels  +  TSMA section header
    # =========================================================
    _fth = F(bg_color=BG_TSMA_HDR)           # TSMA header bg, no bold
    _fth_b = F(bold=True, bg_color=BG_TSMA_HDR)  # TSMA header bg, bold
    set_row_props(ws, 4, height=17, fmt=_fth)
    write(ws, 4, COL_B, "TSMA", _fth_b)
    for i, lbl in enumerate(MONTH_LABELS):
        write(ws, 4, FIRST_MONTH + i, lbl, _fth)

    # =========================================================
    # ROWS 5-10: TSMA summary rows
    # =========================================================
    _fth_tot = F(bold=True, bg_color=BG_TSMA_HDR)

    for r, h in [(5, 17), (6, 17), (7, 17), (8, 17), (9, 17), (10, 17)]:
        set_row_props(ws, r, height=h, fmt=_fth)

    write(ws, 5, COL_B, "Cellular", _fth)
    write_monthly_ref(ws, 5, ROW_TSMA_TOTAL_CEL, _fth)
    write_summary_cols(ws, 5, "Cellular")

    write(ws, 6, COL_B, "Data", _fth)
    write_monthly_ref(ws, 6, ROW_TSMA_TOTAL_DAT, _fth)
    write_summary_cols(ws, 6, "Data")

    write(ws, 7, COL_B, "Voice", _fth)
    write_monthly_ref(ws, 7, ROW_TSMA_TOTAL_VOI, _fth)
    write_summary_cols(ws, 7, "Voice")

    write(ws, 8, COL_B, "Out of Scope", _fth)
    write_monthly_ref(ws, 8, ROW_TSMA_TOTAL_OOS, _fth)

    write(ws, 9, COL_B, "Total", _fth_tot)
    write_monthly_sum_range(ws, 9, 5, 8, _fth_tot)

    write(ws, 10, COL_B, "MMS", _fth)
    write_monthly_ref(ws, 10, ROW_TSMA_TOTAL_MMS, _fth)
    write_summary_cols(ws, 10, "MMS")

    # =========================================================
    # ROWS 11-90: TSMA BGE detail  (outline level 1)
    # =========================================================
    _ftb    = F(bg_color=BG_TSMA_BGE)             # TSMA BGE bg, plain
    _ftb_b  = F(bold=True, bg_color=BG_TSMA_BGE)  # TSMA BGE bg, bold
    _ftb_ivr = F(bg_color=BG_IVR)                 # Voice-IVR override

    # Row 11 – "BGEs" header
    set_row_props(ws, 11, fmt=_fth, opts={"level": 1})
    write(ws, 11, COL_A, "BGEs", _fth_b)

    for bge_name, a_label, a2_label in zip(BGES, BGE_A_LABELS, BGE_A2_LABELS):
        rows_def = TSMA_BGE_ROWS[bge_name if bge_name != "VCHA\n(+PHC)" else "VCHA"]
        bge_row_map = TSMA_ROW_MAP[bge_name if bge_name != "VCHA\n(+PHC)" else "VCHA"]
        first_r = min(bge_row_map.values())
        last_r  = max(bge_row_map.values())

        for label, rtype in rows_def:
            r = bge_row_map[rtype]
            if rtype == "voice_ivr":
                row_bg, fmt_cell = _ftb_ivr, _ftb_ivr
            elif rtype == "total":
                row_bg, fmt_cell = _ftb, _ftb_b
            else:
                row_bg, fmt_cell = _ftb, _ftb
            set_row_props(ws, r, height=17, fmt=row_bg, opts={"level": 1})
            if r == first_r:
                write(ws, r, COL_A, a_label, row_bg)
                if a2_label and r + 1 < last_r:
                    write(ws, r + 1, COL_A, a2_label, _ftb)
            write(ws, r, COL_B, label, fmt_cell)
            if rtype == "total":
                write_monthly_sum_range(ws, r, first_r, last_r - 1, _ftb_b)

    # TSMA TOTAL aggregate rows (86-90)
    for r in range(86, 91):
        set_row_props(ws, r, height=17, fmt=_fth, opts={"level": 1})

    write(ws, ROW_TSMA_TOTAL_CEL, COL_B, "TOTAL Cellular", _fth)
    write_monthly_sum_rows(ws, ROW_TSMA_TOTAL_CEL, TSMA_CEL_ROWS, _fth)

    write(ws, ROW_TSMA_TOTAL_MMS, COL_B, "TOTAL MMS", _fth)
    write_monthly_sum_rows(ws, ROW_TSMA_TOTAL_MMS, TSMA_MMS_ROWS, _fth)

    write(ws, ROW_TSMA_TOTAL_DAT, COL_B, "TOTAL Data", _fth)
    write_monthly_sum_rows(ws, ROW_TSMA_TOTAL_DAT, TSMA_DAT_ROWS, _fth)

    write(ws, ROW_TSMA_TOTAL_VOI, COL_B, "TOTAL Voice", _fth)
    write_monthly_sum_rows(ws, ROW_TSMA_TOTAL_VOI, TSMA_VOI_ROWS, _fth)

    write(ws, ROW_TSMA_TOTAL_OOS, COL_B, "TOTAL OoS", _fth)
    write_monthly_sum_rows(ws, ROW_TSMA_TOTAL_OOS, TSMA_OOS_ROWS, _fth)

    # =========================================================
    # ROW 91: TSMA + NGTAs combined totals
    # =========================================================
    _fcomb = F(bg_color=BG_COMBINED)
    set_row_props(ws, 91, height=16, fmt=_fcomb)
    write(ws, 91, 13, "TSMA+NGTAs", _fcomb)   # col N
    write_monthly_formula(
        ws, 91,
        lambda c: f"={col_letter(c)}{ROW_TSMA_SUM_TOT}"
                  f"+{col_letter(c)}115"
                  f"+{col_letter(c)}217",
        _fcomb,
    )

    # =========================================================
    # ROWS 92-108: Hidden sub-aggregate rows
    # =========================================================
    _hidden = {"hidden": True}

    # Gov + ECC  (rows 92-94)
    gov_r   = TSMA_ROW_MAP["Gov BC"]
    ecc_r   = TSMA_ROW_MAP["ECC"]
    for r, label, r1, r2 in [
        (92, "Cellular", gov_r["cellular"], ecc_r["cellular"]),
        (93, "Data",     gov_r["data"],     ecc_r["data"]),
        (94, "Voice",    gov_r["voice"],     ecc_r["voice"]),
    ]:
        set_row_props(ws, r, height=17, fmt=_ftb, opts=_hidden)
        write(ws, r, COL_B, label, _ftb)
        write_monthly_formula(ws, r, lambda c, _r1=r1, _r2=r2:
                              f"={col_letter(c)}{_r1}+{col_letter(c)}{_r2}", _ftb)
        write(ws, r, COL_AM, "Gov & ECC", _ftb)
        write(ws, r, COL_AN, label, _ftb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    set_row_props(ws, 95, height=16, fmt=_ftb, opts=_hidden)

    # Health authorities  (rows 96-99)
    health_bges = ["FHA","NHA","ICBC","PHSA","IHA","VIHA","FNHA","VCHA"]
    _hcel = [TSMA_ROW_MAP[b]["cellular"] for b in health_bges]
    _hmms = [TSMA_ROW_MAP[b]["mms"] for b in ["FHA","PHSA","VCHA"]]
    _hdat = [TSMA_ROW_MAP[b]["data"]     for b in health_bges]
    _hvoi = [TSMA_ROW_MAP[b]["voice"]    for b in health_bges]
    for r, label, rows_list in [
        (96, "Cellular", _hcel),
        (97, "MMS",      _hmms),
        (98, "Data",     _hdat),
        (99, "Voice",    _hvoi),
    ]:
        set_row_props(ws, r, height=17, fmt=_ftb, opts=_hidden)
        write(ws, r, COL_B, label, _ftb)
        write_monthly_sum_rows(ws, r, rows_list, _ftb)
        write(ws, r, COL_AM, "Health", _ftb)
        write(ws, r, COL_AN, label, _ftb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    set_row_props(ws, 100, height=16, fmt=_ftb, opts=_hidden)

    # Crown corps  (rows 101-103)
    crown_bges = ["BCLC","BC Hydro","WSBC","ICBC"]
    _ccel = [TSMA_ROW_MAP[b]["cellular"] for b in crown_bges]
    _cdat = [TSMA_ROW_MAP[b]["data"]     for b in crown_bges]
    _cvoi = [TSMA_ROW_MAP[b]["voice"]    for b in crown_bges]
    for r, label, rows_list in [
        (101, "Cellular", _ccel),
        (102, "Data",     _cdat),
        (103, "Voice",    _cvoi),
    ]:
        set_row_props(ws, r, height=17, fmt=_ftb, opts=_hidden)
        write(ws, r, COL_B, label, _ftb)
        write_monthly_sum_rows(ws, r, rows_list, _ftb)
        write(ws, r, COL_AM, "Crown Corps", _ftb)
        write(ws, r, COL_AN, label, _ftb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    set_row_props(ws, 104, height=16, fmt=_ftb, opts=_hidden)

    # School Districts  (rows 105-107)
    sd_r = TSMA_ROW_MAP["School Districts"]
    for r, label, target in [
        (105, "Cellular", sd_r["cellular"]),
        (106, "Data",     sd_r["data"]),
        (107, "Voice",    sd_r["voice"]),
    ]:
        set_row_props(ws, r, height=17, fmt=_ftb, opts=_hidden)
        write(ws, r, COL_B, label, _ftb)
        write_monthly_ref(ws, r, target, _ftb)
        write(ws, r, COL_AM, "School Districts", _ftb)
        write(ws, r, COL_AN, label, _ftb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    set_row_props(ws, 108, fmt=_ftb, opts=_hidden)

    # Separator row 109 – bright cyan
    _fsep = F(bg_color=BG_SEPARATOR)
    set_row_props(ws, 109, height=16, fmt=_fsep)

    # =========================================================
    # ROWS 110-190: TELUS NGTA section
    # =========================================================
    _ftelh   = F(bg_color=BG_TELUS_HDR)
    _ftelh_b = F(bold=True, bg_color=BG_TELUS_HDR)
    _ftelb   = F(bg_color=BG_TELUS_BGE)
    _ftelb_b = F(bold=True, bg_color=BG_TELUS_BGE)

    set_row_props(ws, 110, height=16, fmt=_ftelh)
    write(ws, 110, COL_B, "TELUS NGTA", _ftelh_b)

    # Summary rows 111-115
    for r, label, tot_row in [
        (111, "Cellular Plans", ROW_TELUS_TOT_PLANS),
        (112, "Cellular H/W",   ROW_TELUS_TOT_HW),
        (113, "Data",           ROW_TELUS_TOT_DAT),
        (114, "Voice",          ROW_TELUS_TOT_VOI),
    ]:
        set_row_props(ws, r, height=17, fmt=_ftelh)
        write(ws, r, COL_B, label, _ftelh)
        write_monthly_ref(ws, r, tot_row, _ftelh)
        write(ws, r, COL_AN, label)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    set_row_props(ws, 115, height=17, fmt=_ftelh)
    write(ws, 115, COL_B, "Total", _ftelh_b)
    write_monthly_sum_range(ws, 115, 111, 114, _ftelh_b)

    # Row 116 – BGEs header (level 1)
    set_row_props(ws, 116, fmt=_ftelh, opts={"level": 1})
    write(ws, 116, COL_A, "BGEs", _ftelh_b)

    # BGE detail rows 117-186
    for bge_name, a_label, a2_label in zip(BGES, BGE_A_LABELS, BGE_A2_LABELS):
        bge_key = bge_name if bge_name != "VCHA\n(+PHC)" else "VCHA"
        bge_rm  = TELUS_ROW_MAP[bge_key]
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

    # TELUS NGTA TOTAL rows 187-190
    for r, label, rows_list in [
        (ROW_TELUS_TOT_PLANS, "TOTAL Cellular Plans", TELUS_PLANS_ROWS),
        (ROW_TELUS_TOT_HW,    "TOTAL Cellular H/W",   TELUS_HW_ROWS),
        (ROW_TELUS_TOT_DAT,   "TOTAL Data",            TELUS_DAT_ROWS),
        (ROW_TELUS_TOT_VOI,   "TOTAL Voice",           TELUS_VOI_ROWS),
    ]:
        set_row_props(ws, r, height=17, fmt=_ftelh)
        write(ws, r, COL_B, label, _ftelh)
        write_monthly_sum_rows(ws, r, rows_list, _ftelh)
        write(ws, r, COL_AN, label.replace("TOTAL ", ""))
        write_f(ws, r, COL_AR, q_sum(r, Y2025[0], Y2025[2]))
        write_f(ws, r, COL_AS, q_sum(r, Y2025[9], Y2025[11]))

    # =========================================================
    # ROWS 191-211: Hidden TELUS sub-aggregates
    # =========================================================
    set_row_props(ws, 191, height=16, fmt=_ftelb, opts=_hidden)

    telus_gov_r = TELUS_ROW_MAP["Gov BC"]
    telus_ecc_r = TELUS_ROW_MAP["ECC"]
    for r, label, rtype in [
        (192, "Cellular",    "cell_plans"),
        (193, "Cellular H/W","cell_hw"),
        (194, "Data",         "data"),
        (195, "Voice",        "voice"),
    ]:
        set_row_props(ws, r, height=17, fmt=_ftelb, opts=_hidden)
        write(ws, r, COL_B, label, _ftelb)
        write_monthly_formula(ws, r, lambda c, rt=rtype:
            f"={col_letter(c)}{telus_gov_r[rt]}+{col_letter(c)}{telus_ecc_r[rt]}", _ftelb)
        write(ws, r, COL_AM, "Gov & ECC", _ftelb)
        write(ws, r, COL_AN, label, _ftelb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    set_row_props(ws, 196, height=16, fmt=_ftelb, opts=_hidden)

    telus_health = ["FHA","NHA","ICBC","PHSA","IHA","VIHA","FNHA","VCHA"]
    for r, label, rtype in [
        (197, "Cellular",    "cell_plans"),
        (198, "Cellular H/W","cell_hw"),
        (199, "Data",         "data"),
        (200, "Voice",        "voice"),
    ]:
        set_row_props(ws, r, height=17, fmt=_ftelb, opts=_hidden)
        write(ws, r, COL_B, label, _ftelb)
        rows_list = [TELUS_ROW_MAP[b][rtype] for b in telus_health]
        write_monthly_sum_rows(ws, r, rows_list, _ftelb)
        write(ws, r, COL_AM, "Health", _ftelb)
        write(ws, r, COL_AN, label, _ftelb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    set_row_props(ws, 201, height=16, fmt=_ftelb, opts=_hidden)

    telus_crown = ["BCLC","BC Hydro","WSBC","ICBC"]
    for r, label, rtype in [
        (202, "Cellular",    "cell_plans"),
        (203, "Cellular H/W","cell_hw"),
        (204, "Data",         "data"),
        (205, "Voice",        "voice"),
    ]:
        set_row_props(ws, r, height=17, fmt=_ftelb, opts=_hidden)
        write(ws, r, COL_B, label, _ftelb)
        rows_list = [TELUS_ROW_MAP[b][rtype] for b in telus_crown]
        write_monthly_sum_rows(ws, r, rows_list, _ftelb)
        write(ws, r, COL_AM, "Crown Corps", _ftelb)
        write(ws, r, COL_AN, label, _ftelb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    set_row_props(ws, 206, height=16, fmt=_ftelb, opts=_hidden)

    telus_sd_r = TELUS_ROW_MAP["School Districts"]
    for r, label, rtype in [
        (207, "Cellular",    "cell_plans"),
        (208, "Cellular H/W","cell_hw"),
        (209, "Data",         "data"),
        (210, "Voice",        "voice"),
    ]:
        set_row_props(ws, r, height=17, fmt=_ftelb, opts=_hidden)
        write(ws, r, COL_B, label, _ftelb)
        write_monthly_ref(ws, r, telus_sd_r[rtype], _ftelb)
        write(ws, r, COL_AM, "School Districts", _ftelb)
        write(ws, r, COL_AN, label, _ftelb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    # Separator row 211 – bright cyan
    set_row_props(ws, 211, height=16, fmt=_fsep)

    # =========================================================
    # ROWS 212-292: Rogers NGTA section
    # =========================================================
    _frogh   = F(bg_color=BG_ROGERS_HDR)
    _frogh_b = F(bold=True, bg_color=BG_ROGERS_HDR)
    _frogb   = F(bg_color=BG_ROGERS_BGE)
    _frogb_b = F(bold=True, bg_color=BG_ROGERS_BGE)

    set_row_props(ws, 212, height=16, fmt=_frogh)
    write(ws, 212, COL_B, "Rogers NGTA", _frogh_b)

    # Summary rows 213-217
    for r, label, tot_row in [
        (213, "Cellular Plans", ROW_ROGERS_TOT_PLANS),
        (214, "Cellular H/W",   ROW_ROGERS_TOT_HW),
        (215, "Data",           ROW_ROGERS_TOT_DAT),
        (216, "Voice",          ROW_ROGERS_TOT_VOI),
    ]:
        set_row_props(ws, r, height=17, fmt=_frogh)
        write(ws, r, COL_B, label, _frogh)
        write_monthly_ref(ws, r, tot_row, _frogh)
        write(ws, r, COL_AN, label)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    set_row_props(ws, 217, height=17, fmt=_frogh)
    write(ws, 217, COL_B, "Total", _frogh_b)
    write_monthly_sum_range(ws, 217, 213, 216, _frogh_b)

    # Row 218 – BGEs header
    set_row_props(ws, 218, fmt=_frogh, opts={"level": 1})
    write(ws, 218, COL_A, "BGEs", _frogh_b)

    # BGE detail rows 219-288
    for bge_name, a_label, a2_label in zip(BGES, BGE_A_LABELS, BGE_A2_LABELS):
        bge_key = bge_name if bge_name != "VCHA\n(+PHC)" else "VCHA"
        bge_rm  = ROGERS_ROW_MAP[bge_key]
        first_r = bge_rm["cell_plans"]
        last_r  = bge_rm["total"]

        for label, rtype in NGTA_BGE_ROWS:
            r = bge_rm[rtype]
            set_row_props(ws, r, height=17, fmt=_frogb, opts={"level": 1})
            if r == first_r:
                write(ws, r, COL_A, a_label, _frogb)
                if a2_label:
                    write(ws, r + 1, COL_A, a2_label, _frogb)
            fmt_cell = _frogb_b if rtype == "total" else _frogb
            write(ws, r, COL_B, label, fmt_cell)
            if rtype == "total":
                write_monthly_sum_range(ws, r, first_r, last_r - 1, _frogb_b)

    # Rogers NGTA TOTAL rows 289-292
    for r, label, rows_list in [
        (ROW_ROGERS_TOT_PLANS, "TOTAL Cellular Plans", ROGERS_PLANS_ROWS),
        (ROW_ROGERS_TOT_HW,    "TOTAL Cellular H/W",   ROGERS_HW_ROWS),
        (ROW_ROGERS_TOT_DAT,   "TOTAL Data",            ROGERS_DAT_ROWS),
        (ROW_ROGERS_TOT_VOI,   "TOTAL Voice",           ROGERS_VOI_ROWS),
    ]:
        set_row_props(ws, r, height=17, fmt=_frogh)
        write(ws, r, COL_B, label, _frogh)
        write_monthly_sum_rows(ws, r, rows_list, _frogh)
        write(ws, r, COL_AN, label.replace("TOTAL ", ""))
        write_f(ws, r, COL_AR, q_sum(r, 13, 15))
        write_f(ws, r, COL_AS, q_sum(r, Y2025[9], Y2025[11]))

    # =========================================================
    # ROWS 293-313: Hidden Rogers sub-aggregates
    # =========================================================
    set_row_props(ws, 293, height=16, fmt=_frogb, opts=_hidden)

    rogers_gov_r = ROGERS_ROW_MAP["Gov BC"]
    rogers_ecc_r = ROGERS_ROW_MAP["ECC"]
    for r, label, rtype in [
        (294, "Cellular",    "cell_plans"),
        (295, "Cellular H/W","cell_hw"),
        (296, "Data",         "data"),
        (297, "Voice",        "voice"),
    ]:
        set_row_props(ws, r, height=17, fmt=_frogb, opts=_hidden)
        write(ws, r, COL_B, label, _frogb)
        write_monthly_formula(ws, r, lambda c, rt=rtype:
            f"={col_letter(c)}{rogers_gov_r[rt]}+{col_letter(c)}{rogers_ecc_r[rt]}", _frogb)
        write(ws, r, COL_AM, "Gov & ECC", _frogb)
        write(ws, r, COL_AN, label, _frogb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    set_row_props(ws, 298, height=16, fmt=_frogb, opts=_hidden)

    rogers_health = ["FHA","NHA","ICBC","PHSA","IHA","VIHA","FNHA","VCHA"]
    for r, label, rtype in [
        (299, "Cellular",    "cell_plans"),
        (300, "Cellular H/W","cell_hw"),
        (301, "Data",         "data"),
        (302, "Voice",        "voice"),
    ]:
        set_row_props(ws, r, height=17, fmt=_frogb, opts=_hidden)
        write(ws, r, COL_B, label, _frogb)
        rows_list = [ROGERS_ROW_MAP[b][rtype] for b in rogers_health]
        write_monthly_sum_rows(ws, r, rows_list, _frogb)
        write(ws, r, COL_AM, "Health", _frogb)
        write(ws, r, COL_AN, label, _frogb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    set_row_props(ws, 303, height=16, fmt=_frogb, opts=_hidden)

    rogers_crown = ["BCLC","BC Hydro","WSBC","ICBC"]
    for r, label, rtype in [
        (304, "Cellular",    "cell_plans"),
        (305, "Cellular H/W","cell_hw"),
        (306, "Data",         "data"),
        (307, "Voice",        "voice"),
    ]:
        set_row_props(ws, r, height=17, fmt=_frogb, opts=_hidden)
        write(ws, r, COL_B, label, _frogb)
        rows_list = [ROGERS_ROW_MAP[b][rtype] for b in rogers_crown]
        write_monthly_sum_rows(ws, r, rows_list, _frogb)
        write(ws, r, COL_AM, "Crown Corps", _frogb)
        write(ws, r, COL_AN, label, _frogb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    set_row_props(ws, 308, height=16, fmt=_frogb, opts=_hidden)

    rogers_sd_r = ROGERS_ROW_MAP["School Districts"]
    for r, label, rtype in [
        (309, "Cellular",    "cell_plans"),
        (310, "Cellular H/W","cell_hw"),
        (311, "Data",         "data"),
        (312, "Voice",        "voice"),
    ]:
        set_row_props(ws, r, height=17, fmt=_frogb, opts=_hidden)
        write(ws, r, COL_B, label, _frogb)
        write_monthly_ref(ws, r, rogers_sd_r[rtype], _frogb)
        write(ws, r, COL_AM, "School Districts", _frogb)
        write(ws, r, COL_AN, label, _frogb)
        write_f(ws, r, COL_AO, annual_sum(r, Y2024))
        write_f(ws, r, COL_AP, annual_sum(r, Y2025))

    set_row_props(ws, 313, height=16)
    # Separator row 314 – bright cyan
    set_row_props(ws, 314, height=16, fmt=_fsep)

    # =========================================================
    # ROWS 315-344: Out of Scope section
    # =========================================================
    set_row_props(ws, 315, height=16)
    write(ws, 315, COL_B, "Out of Scope", f_section)
    write(ws, 315, COL_AO, 2024, f_bold)
    write(ws, 315, COL_AP, 2025, f_bold)
    write(ws, 315, COL_AQ, "Q1 2024", f_bold)
    write(ws, 315, COL_AR, "Q1 2025", f_bold)
    write(ws, 315, COL_AS, "Q4 2025", f_bold)

    # --- Managed Router ---
    set_row_props(ws, 316, height=16)
    write(ws, 316, COL_B, "Managed Router")
    write(ws, 316, COL_AO, "Jan-Dec")

    oos_mr_orgs = [
        "CHILDRENS & WOMENS HEALTH CENTRE OF BC SOCIETY",
        "FIRST NATIONS HEALTH AUTHORITY",
        "GBC - MINISTRY OF CITIZENS SERVICES",
        "GBC - SHARED SERVICES BC",
        "GBC - MINISTRY OF EDUCATION & CHILD CARE",
        "BRITISH COLUMBIA LIQUOR DISTRIBUTION BRANCH",
        "GBC - LIQUOR DISTRIBUTION BRANCH",
    ]
    for r, org in zip(OOS_MANAGED_ROUTER_ROWS, oos_mr_orgs):
        set_row_props(ws, r, height=17, opts={"level": 1})
        write(ws, r, COL_B, org)

    set_row_props(ws, 324, height=17)
    write(ws, 324, COL_B, "Total", f_total)
    write_monthly_sum_range(ws, 324, 317, 323, f_total)

    # --- Managed WLAN / Managed Wi-Fi ---
    set_row_props(ws, 325, height=17)
    write(ws, 325, COL_B, "Managed WLAN/Managed Wi-Fi")

    oos_wlan_orgs = [
        "VANCOUVER COASTAL HEALTH AUTHORITY O/A OLIVE DEVAUD RESIDENCE",
        "VANCOUVER COASTAL HEALTH AUTHORITY O/A LIONS GATE HOSPITAL",
        "VANCOUVER COASTAL HEALTH AUTHORITY HOWE SOUND HOME SUPPORT SERVICES",
        "VANCOUVER COASTAL HEALTH AUTHORITY",
        "PROVINCIAL HEALTH SERVICES AUTHORITY",
        "GREATER VANCOUVER MENTAL HEALTH SERVICE",
    ]
    for r, org in zip(OOS_MANAGED_WLAN_ROWS, oos_wlan_orgs):
        set_row_props(ws, r, height=17, opts={"level": 1})
        write(ws, r, COL_B, org)

    set_row_props(ws, 332, height=17)
    write(ws, 332, COL_B, "Total", f_total)
    write_monthly_sum_range(ws, 332, 326, 331, f_total)

    # --- Managed Security / Managed Firewall ---
    set_row_props(ws, 333, height=17)
    write(ws, 333, COL_B, "Managed Security/Managed Firewall")

    oos_sec_orgs = [
        "BRITISH COLUMBIA HYDRO & POWER AUTHORITY",
        "WORKERS COMPENSATION BOARD OF BRITISH COLUMBIA",
        "INSURANCE CORPORATION OF BRITISH COLUMBIA - ICBC",
        "FRASER HEALTH AUTHORITY",
        "GBC - MINISTRY OF EDUCATION & CHILD CARE",
        "PROVINCIAL HEALTH SERVICES AUTHORITY",
        "GBC - MINISTRY OF CITIZENS SERVICES",
        "FIRST NATIONS HEALTH AUTHORITY",
        "GBC - OFFICE OF THE CHIEF INFORMATION OFFICER",
        "GBC - MINISTRY OF HEALTH",
    ]
    for r, org in zip(OOS_MANAGED_SEC_ROWS, oos_sec_orgs):
        set_row_props(ws, r, height=17, opts={"level": 1})
        write(ws, r, COL_B, org)

    set_row_props(ws, 344, height=17)
    write(ws, 344, COL_B, "Total", f_total)
    # Original sums 335:343 (skips row 334 which is the first org but matches formula)
    write_monthly_sum_range(ws, 344, 335, 343, f_total)

    set_row_props(ws, 345, height=16)

    # =========================================================
    # ROWS 346-354: TSMA Lite  (quarterly data)
    # =========================================================
    set_row_props(ws, 346, height=16)
    write(ws, 346, COL_B, "TSMA Lite", f_section)

    for r, label in [
        (ROW_TSMALITE_VOICE,  "Voice - Total Charges"),
        (ROW_TSMALITE_DATA,   "Data - Total Charges"),
        (ROW_TSMALITE_OTHER,  "*Other Charges & Credits"),
        (ROW_TSMALITE_CELUE,  "Cellular User Equipment Cost"),
    ]:
        set_row_props(ws, r, height=17)
        write(ws, r, COL_B, label)
        # Data input: leave quarterly cells empty for now

    # Row 351: SUM totals per quarter-end column
    set_row_props(ws, ROW_TSMALITE_TOTAL, height=17)
    for col in TSMA_LITE_Q_COLS:
        write_f(ws, ROW_TSMALITE_TOTAL, col,
                sum_range(ROW_TSMALITE_VOICE, ROW_TSMALITE_CELUE, col), f_total)

    set_row_props(ws, 352, height=17)   # blank separator

    # Row 353: Voice + Data + Other (excludes cellular UE)
    set_row_props(ws, ROW_TSMALITE_EXC, height=17)
    for col in TSMA_LITE_Q_COLS:
        cl = col_letter(col)
        write_f(ws, ROW_TSMALITE_EXC, col,
                f"={cl}{ROW_TSMALITE_VOICE}+{cl}{ROW_TSMALITE_DATA}+{cl}{ROW_TSMALITE_OTHER}")

    # Row 354: Cellular UE reference
    set_row_props(ws, ROW_TSMALITE_CELUE2, height=17)
    for col in TSMA_LITE_Q_COLS:
        write_f(ws, ROW_TSMALITE_CELUE2, col,
                ref_cell(ROW_TSMALITE_CELUE, col))

    # =========================================================
    # Freeze the first two columns (A and B) and top 4 rows
    # =========================================================
    ws.freeze_panes(4, 2)

    wb.close()
    print(f"✓ Written → {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
