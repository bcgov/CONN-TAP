"""Shared constants, colours, formula builders, and sheet-writing helpers.

Imported by build_spend_sheet.py, telus_ngta.py, and build_telus_ngta.py.
"""

# ---------------------------------------------------------------------------
# Theme color resolution
# ---------------------------------------------------------------------------
# Base hex values from xl/theme/theme1.xml.
# The fill `theme` attribute uses OOXML ordering where theme=3 → dk2 (Text 2).
_THEME_BASE = {
    3: "64A3E3",   # accent 1 - dark blue
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


BG_TSMA_HDR   = _tint(_THEME_BASE[3], 0.750)   
BG_TSMA_BGE   = _tint(_THEME_BASE[3], 0.900)   
BG_COMBINED   = _tint(_THEME_BASE[6], 0.600)   # #A3C4A7
BG_SEPARATOR  = "#00B0F0"
BG_TELUS_HDR  = _tint(_THEME_BASE[8], 0.600)   # #D9AAD4
BG_TELUS_BGE  = _tint(_THEME_BASE[8], 0.800)   # #ECD5E9
BG_ROGERS_HDR = _tint(_THEME_BASE[5], 0.600)   # #F6C6AD
BG_ROGERS_BGE = _tint(_THEME_BASE[5], 0.800)   # #FBE3D6
BG_IVR        = "#FFA7A7"


# Standard dollar format: positive → $1,234.56 ; negative → ($1,234.56) in red
NUM_FMT = '$#,##0.00;[Red]($#,##0.00)'


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

    def n(self, **props):
        """Like __call__ but always includes the dollar/red-negative number format."""
        return self(**props, num_format=NUM_FMT)


# ---------------------------------------------------------------------------
# Column index constants (0-based)
# ---------------------------------------------------------------------------
COL_A = 0
COL_B = 1
FIRST_MONTH = 2
LAST_MONTH  = 37
MONTH_COLS  = list(range(FIRST_MONTH, LAST_MONTH + 1))

Y2024 = list(range(2,  14))
Y2025 = list(range(14, 26))
Y2026 = list(range(26, 38))

COL_AM = 38   # group label (visible)
COL_AN = 39   # row label   (hidden)
COL_AO = 40   # 2024 annual (hidden)
COL_AP = 41   # 2025 annual (hidden)
COL_AQ = 42   # Q1 2024    (visible)
COL_AR = 43   # Q1 2025    (hidden)
COL_AS = 44   # Q4 2025    (hidden)

TSMA_LITE_Q_COLS = [4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34, 37]

_MNAMES = ['Jan','Feb','Mar','Apr','May','Jun',
           'Jul','Aug','Sep','Oct','Nov','Dec']
MONTH_LABELS = []
for _yr in [2024, 2025, 2026]:
    for _mi, _mn in enumerate(_MNAMES):
        MONTH_LABELS.append(
            f"{'Sept' if (_yr == 2024 and _mi == 8) else _mn} {_yr}"
        )

# ---------------------------------------------------------------------------
# BGE data (shared across TSMA, TELUS NGTA, Rogers NGTA)
# ---------------------------------------------------------------------------
BGES = [
    "Gov BC", "BCLC", "BC Hydro", "WSBC", "ECC", "FHA",
    "NHA", "ICBC", "PHSA", "IHA", "VIHA", "FNHA",
    "VCHA\n(+PHC)", "School Districts",
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

NGTA_BGE_ROWS = [
    ('Cellular Plans', 'cell_plans'),
    ('Cellular H/W',   'cell_hw'),
    ('Data',           'data'),
    ('Voice',          'voice'),
    ('Other',          'other'),
    ('Total',          'total'),
]


def _build_ngta_row_map(start_row: int):
    """Return ({bge_name: {row_type: row_number}}, next_free_row) with 6 rows per BGE."""
    row_map = {}
    r = start_row
    for bge in BGE_A_LABELS:
        row_map[bge] = {}
        for _label, rtype in NGTA_BGE_ROWS:
            row_map[bge][rtype] = r
            r += 1
    return row_map, r


def _ngta_rows_by_type(row_map, rtype):
    return [row_map[b][rtype] for b in BGE_A_LABELS if rtype in row_map[b]]


# ---------------------------------------------------------------------------
# Column letter helpers
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
    return f"{col_letter(col_0)}{row_1}"


# ---------------------------------------------------------------------------
# Formula builders
# ---------------------------------------------------------------------------
def sum_rows(rows, col) -> str:
    cl = col_letter(col)
    return "=" + "+".join(f"{cl}{r}" for r in rows)


def sum_range(r1, r2, col) -> str:
    cl = col_letter(col)
    return f"=SUM({cl}{r1}:{cl}{r2})"


def ref_cell(target_row, col) -> str:
    return f"={col_letter(col)}{target_row}"


def annual_sum(row, year_cols) -> str:
    return f"=SUM({col_letter(year_cols[0])}{row}:{col_letter(year_cols[-1])}{row})"


def q_sum(row, q_start_col, q_end_col) -> str:
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
    for col in MONTH_COLS:
        write_f(ws, row_1, col, formula_fn(col), fmt)


def write_monthly_ref(ws, row_1: int, target_row: int, fmt=None):
    write_monthly_formula(ws, row_1, lambda c: ref_cell(target_row, c), fmt)


def write_monthly_sum_rows(ws, row_1: int, rows, fmt=None):
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
        write_f(ws, row_1, COL_AQ, q_sum(row_1, Y2024[0], Y2024[2]))
        write_f(ws, row_1, COL_AR, q_sum(row_1, Y2025[0], Y2025[2]))
        write_f(ws, row_1, COL_AS, q_sum(row_1, Y2025[9], Y2025[11]))


# ---------------------------------------------------------------------------
# Workbook-level setup helpers
# ---------------------------------------------------------------------------
def set_column_widths(ws):
    """Apply the standard column widths used by all spend-tracking sheets."""
    ws.set_column(COL_A, COL_A, 10.5)
    ws.set_column(COL_B, COL_B, 43.0)
    ws.set_column(FIRST_MONTH, LAST_MONTH, 10.5)
    ws.set_column(11, 11, 11.5)
    ws.set_column(18, 18, 11.17)
    ws.set_column(26, 26, 10.83)
    ws.set_column(28, 28, 8.83)
    ws.set_column(29, 29, 8.5)
    ws.set_column(30, 30, 9.0)
    ws.set_column(31, 31, 8.5)
    ws.set_column(32, 32, 7.83)
    ws.set_column(33, 33, 8.66)
    ws.set_column(34, 34, 8.5)
    ws.set_column(COL_AM, COL_AM, 13.5)
    ws.set_column(COL_AN, COL_AN, 13.5, None, {"hidden": True})
    ws.set_column(COL_AO, COL_AO, 13.33, None, {"hidden": True})
    ws.set_column(COL_AP, COL_AP, 12.0,  None, {"hidden": True})
    ws.set_column(COL_AQ, COL_AQ, 11.5)
    ws.set_column(COL_AR, COL_AR, 11.5,  None, {"hidden": True})
    ws.set_column(COL_AS, COL_AS, 9.83,  None, {"hidden": True})


def write_year_quarter_headers(ws, F):
    """Write rows 1-3: year spans, calendar quarters, fiscal quarters."""
    f_bold = F(bold=True)
    set_row_props(ws, 3, height=16)

    merge(ws, 1, 2,  1, 13, 2024, f_bold)
    merge(ws, 1, 14, 1, 25, 2025, f_bold)
    merge(ws, 1, 26, 1, 37, 2026, f_bold)

    cq = ["CQ1", "CQ2", "CQ3", "CQ4"]
    for yr_start in [2, 14, 26]:
        for qi, label in enumerate(cq):
            c = yr_start + qi * 3
            merge(ws, 2, c, 2, c + 2, label, f_bold)
    write(ws, 2, COL_AO, 2024,      f_bold)
    write(ws, 2, COL_AP, 2025,      f_bold)
    write(ws, 2, COL_AQ, "Q1 2024", f_bold)
    write(ws, 2, COL_AR, "Q1 2025", f_bold)
    write(ws, 2, COL_AS, "Q4 2025", f_bold)

    fq = ["FQ4", "FQ1", "FQ2", "FQ3"]
    for yr_start in [2, 14, 26]:
        for qi, label in enumerate(fq):
            c = yr_start + qi * 3
            merge(ws, 3, c, 3, c + 2, label, f_bold)
    write(ws, 3, COL_AO, "Jan-Dec")


def write_month_label_row(ws, row_1: int, fmt=None):
    """Write month labels (Jan 2024 … Dec 2026) across the data columns."""
    for i, lbl in enumerate(MONTH_LABELS):
        write(ws, row_1, FIRST_MONTH + i, lbl, fmt)
