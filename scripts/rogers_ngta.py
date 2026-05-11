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
  first_row + 92-96 : aggregate TOTAL rows (plans / hw / data / voice / other)
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
# Entity-key mapping (case-insensitive, both short codes and full names)
# ---------------------------------------------------------------------------
BGE_MAP = {
    "BCH": "BC Hydro",
    "BC HYDRO": "BC Hydro",
    "BRITISH COLUMBIA HYDRO": "BC Hydro",
    "BRITISH COLUMBIA HYDRO & POWER AUTHORITY": "BC Hydro",
    "BCLC": "BCLC",
    "BC LOTTERY": "BCLC",
    "BC LOTTERY CORPORATION": "BCLC",
    "BRITISH COLOMBIA LOTTERY CORPORATION": "BCLC",
    "BRITISH COLUMBIA LOTTERY CORPORATION": "BCLC",
    "ECC": "ECC",
    "MOE": "ECC",
    "EDUCATION AND CHILD CARE": "ECC",
    "MINISTRY OF EDUCATION": "ECC",
    "MINISTRY OF EDUCATION AND CHILD CARE": "ECC",
    "FHA": "FHA",
    "FRASER HEALTH": "FHA",
    "FRASER HEALTH AUTHORITY": "FHA",
    "FNHA": "FNHA",
    "FIRST NATIONS HEALTH AUTHORITY": "FNHA",
    "GBC": "Gov BC",
    "GOBC": "Gov BC",
    "GOVBC": "Gov BC",
    "GOV BC": "Gov BC",
    "BC GOVERNMENT MINISTRIES": "Gov BC",
    "GOVERNMENT OF BC": "Gov BC",
    "GOVERNMENT OF BRITISH COLUMBIA": "Gov BC",
    "ICBC": "ICBC",
    "INSURANCE CORPORATION OF BRITISH COLUMB.": "ICBC",
    "INSURANCE CORPORATION OF BRITISH COLUMBIA": "ICBC",
    "IHA": "IHA",
    "INTERIOR HEALTH": "IHA",
    "INTERIOR HEALTH AUTHORITY": "IHA",
    "NHA": "NHA",
    "NORTHERN HEALTH": "NHA",
    "NORTHERN HEALTH AUTHORITY": "NHA",
    "PHSA": "PHSA",
    "PROVINCIAL HEALTH SERVICES": "PHSA",
    "PROVINCIAL HEALTH SERVICES AUTHORITY": "PHSA",
    "SD": "School Districts",
    "SCHOOL DISTRICT": "School Districts",
    "SCHOOL DISTRICTS": "School Districts",
    "VCHA": "VCHA",
    "VCHA (+PHC)": "VCHA",
    "VCHA PHC": "VCHA",
    "VANCOUVER COASTAL HEALTH": "VCHA",
    "VANCOUVER COASTAL HEALTH AUTHORITY": "VCHA",
    "PROVIDENCE HEALTH CARE": "VCHA",
    "VIHA": "VIHA",
    "VANCOUVER ISLAND HEALTH": "VIHA",
    "VANCOUVER ISLAND HEALTH AUTHORITY": "VIHA",
    "WSBC": "WSBC",
    "WORKERS COMPENSATION BOARD": "WSBC",
    "WORKERS COMPENSATION BOARD OF BRITISH COLUMBIA": "WSBC",
    "WORKSAFEBC": "WSBC",
}

SUB_BGE_TO_BGE = {
    "BC MIN ATTORNEY GENERAL": "Gov BC",
    "BC MIN CITIZENS' SERVICES": "Gov BC",
    "BC MIN EDUCATION & CHILD CARE": "ECC",
    "BC MIN EDUCATION AND CHILD CARE": "ECC",
    "BC MIN EMERG MGMT & CLIMATE READINESS": "Gov BC",
    "BC MIN ENERGY AND CLIMATE SOLUTIONS": "Gov BC",
    "BC MIN ENVIRONMENT AND PARKS": "Gov BC",
    "BC MIN FORESTS": "Gov BC",
    "BC MIN HEALTH": "Gov BC",
    "BC MIN HOUSING AND MUNICIPAL AFFAIRS": "Gov BC",
    "BC MIN INDIGENOUS RELATIONS & RECONCIL.": "Gov BC",
    "BC MIN JOBS AND ECONOMIC GROWTH": "Gov BC",
    "BC MIN LABOUR": "Gov BC",
    "BC MIN POST-SECONDARY ED & FUTURE SKILLS": "Gov BC",
    "BC MIN SOCIAL DEV & POVERTY REDUCTION": "Gov BC",
    "BC MIN TOURISM, ARTS, CULTURE, AND SPORT": "Gov BC",
    "BC MIN TRANSPORTATION & TRANSIT": "Gov BC",
    "INDIGENOUS RELATIONS AND RECONCILIATION": "Gov BC",
    "JOB ECONOMIC DEVELOPMENT AND INNOVATION": "Gov BC",
    "LAND AND WATER BC INC": "Gov BC",
    "MIN OF FINANCE BC": "Gov BC",
    "MIN OF JOBS TOURISM & INNOVATION": "Gov BC",
    "MIN OF LABOUR": "Gov BC",
    "MINISTRY OF CITIZENS SERVICES": "Gov BC",
    "MINISTRY OF INFRASTRUCTURE": "Gov BC",
    "MIN OF SOCIAL DEVELOPMENT": "Gov BC",
    "OFFICE OF THE PREMIER": "Gov BC",
    "TRANSPORTATION AND TRANSIT": "Gov BC",
}

ENTITY_LOOKUP = {
    alias: bge
    for key, bge in BGE_MAP.items()
    for alias in (key, re.sub(r"[^A-Z0-9]+", "", key))
}
SUB_BGE_LOOKUP = {
    alias: bge
    for key, bge in SUB_BGE_TO_BGE.items()
    for alias in (key, re.sub(r"[^A-Z0-9]+", "", key))
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


def _normalize_key(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).replace("\u00a0", " ").strip()).upper()


def _entity_key(value: object) -> str:
    raw = _normalize_key(value)
    compact = re.sub(r"[^A-Z0-9]+", "", raw)
    return ENTITY_LOOKUP.get(raw) or ENTITY_LOOKUP.get(compact, "")


def _sub_bge_key(value: object) -> str:
    raw = _normalize_key(value)
    compact = re.sub(r"[^A-Z0-9]+", "", raw)
    return SUB_BGE_LOOKUP.get(raw) or SUB_BGE_LOOKUP.get(compact, "")


def _resolve_bge(row: dict[str, str]) -> str:
    bge_raw = row.get("bge") or row.get("entity_key") or row.get("entity") or ""
    sub_raw = row.get("sub_bge") or row.get("sub-bge") or row.get("subbge") or ""

    bge = _normalize_key(bge_raw)
    sub = _normalize_key(sub_raw)
    sub_compact = re.sub(r"[^A-Z0-9]+", "", sub)

    if sub.startswith("SCHOOL DISTRICT") or sub.startswith("DISTRICT"):
        return "School Districts"
    if bge.startswith("SCHOOL DISTRICT") or bge.startswith("DISTRICT"):
        return "School Districts"
    if "FAMILY MAINTENANCE AGENCY" in sub or "PUBLIC SERVICE AGENCY" in sub:
        return "Gov BC"
    if "EDUCATION" in sub and "CHILD" in sub:
        return "ECC"

    sub_mapped = _sub_bge_key(sub)
    if sub_mapped:
        return sub_mapped

    bge_mapped = _entity_key(bge)
    if bge_mapped:
        return bge_mapped

    if sub_compact:
        return _entity_key(sub)
    return ""


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


def _load_summary_row(data: dict[tuple[str, str, int], float], row: dict[str, str]) -> bool:
    bge = _resolve_bge(row)
    col = _month_to_col(_first_value(
        row, "month_start", "month", "billing_month", "invoice_date", "billingdate",
    ))
    if not bge or col is None:
        return False

    loaded = False
    for csv_col, row_type in SPEND_COL_MAP.items():
        val = _amount(row.get(csv_col, ""))
        if val is None:
            continue
        _add(data, bge, row_type, col, val)
        loaded = True
    return loaded


def _load_raw_row(data: dict[tuple[str, str, int], float], row: dict[str, str]) -> bool:
    bge = _resolve_bge(row)
    col = _month_to_col(_first_value(
        row, "month_start", "month", "billing_month", "invoice_date", "billingdate",
    ))
    if not bge or col is None:
        return False

    billed = _amount(_first_value(
        row, "billed_amount_pre_tax", "charges_subtotal", "billed", "amount",
    ))
    hardware = _amount(_first_value(row, "hardware", "cellular_hardware", "cell_hw"))
    product_line = _normalize_key(row.get("productline", ""))

    if product_line:
        if billed is None:
            return False
        if product_line == "VOICE":
            _add(data, bge, "voice", col, billed)
        elif product_line == "DATA":
            _add(data, bge, "data", col, billed)
        else:
            _add(data, bge, "other", col, billed)
        return True

    if hardware is None and billed is None:
        return False

    _add(data, bge, "cell_hw", col, hardware or 0.0)
    if billed is not None:
        _add(data, bge, "cell_plans", col, billed - (hardware or 0.0))
    return True


def load_rogers_ngta(path: str = ROGERS_CSV) -> dict[tuple[str, str, int], float]:
    """Read rogers_ngta_spend.csv and return {(bge_key, row_type, col_idx): value}.

    The preferred format is a monthly summary CSV with one row per BGE/month.
    The loader also accepts Rogers raw export rows when `month_start` is
    present. Raw cellular rows split billed amount into Cellular H/W and
    Cellular Plans, while raw PRODUCTLINE rows fill Voice, Data, or Other.

    Unknown BGEs and dates outside 2024-2026 are skipped. Values for the same
    (bge, row_type, col) are summed.
    """
    data: dict[tuple[str, str, int], float] = {}
    for row in _read_rows(path) or ():
        if not _load_summary_row(data, row):
            _load_raw_row(data, row)
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
    set_row_props(ws, sum_total_r, height=17, fmt=_frogh)
    write(ws, sum_total_r, COL_B, "Total", _frogh_b)
    write_monthly_sum_range(ws, sum_total_r, sum_start, sum_start + 4, _frogh_b)

    # ---- BGEs header ----
    bges_hdr = first_row + 7
    set_row_props(ws, bges_hdr, fmt=_frogh, opts={"level": 1})
    write(ws, bges_hdr, COL_A, "BGEs", _frogh_b)

    # ---- BGE detail rows ----
    for bge_name, a_label, a2_label in zip(BGES, BGE_A_LABELS, BGE_A2_LABELS):
        bge_key = bge_name if bge_name != "VCHA\n(+PHC)" else "VCHA"
        bge_rm = rogers_row_map[bge_key]
        first_r = bge_rm["cell_plans"]
        last_r = bge_rm["total"]

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
        set_row_props(ws, r, height=17, fmt=_frogh)
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
