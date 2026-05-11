#!/usr/bin/env python3
"""
Recreate the spend tracking spreadsheet using xlsxwriter.

Organized into 6 fillable categories:
  1. tsma           – TSMA BGE detail (rows 11-90)
  2. mms            – MMS summary row and within-BGE MMS sub-rows
  3. telus_ngta     – TELUS NGTA BGE detail (rows 118-201, Other row added)
  4. rogers_ngta    – Rogers NGTA BGE detail (rows 240-323, Other row added)
  5. out_of_scope   – Out-of-Scope sub-categories (rows 355-384)
  6. tsma_lite      – TSMA Lite quarterly data (rows 386-394)

Run:  python3 scripts/build_spend_sheet.py
Output: scripts/spend_tracking.xlsx
"""

import xlsxwriter

from sheet_utils import (
    # Colors
    BG_TSMA_HDR, BG_TSMA_BGE, BG_COMBINED, BG_SEPARATOR, BG_IVR,
    _FmtCache,
    # Column constants
    COL_A, COL_B, COL_AM, COL_AN, COL_AO, COL_AP,
    FIRST_MONTH, LAST_MONTH, MONTH_COLS, Y2024, Y2025, TSMA_LITE_Q_COLS,
    # BGE data
    BGES, BGE_A_LABELS, BGE_A2_LABELS,
    # Formula builders
    col_letter, sum_range, ref_cell, annual_sum,
    # Sheet writers
    write, write_f, merge, set_row_props,
    write_monthly_formula, write_monthly_ref,
    write_monthly_sum_rows, write_monthly_sum_range, write_summary_cols,
    # Workbook setup
    set_column_widths, write_year_quarter_headers, write_month_label_row,
)
from telus_ngta import load_telus_ngta, build_telus_ngta_section
from rogers_ngta import load_rogers_ngta, build_rogers_ngta_section
from tsma import load_tsma_data, load_tsma_lite_data, write_tsma_detail_row
from tsma_other import load_tsma_other, build_oos_section

import os
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "spend_tracking.xlsx")

# ---------------------------------------------------------------------------
# TSMA BGE sub-row definitions
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

# ---------------------------------------------------------------------------
# TSMA row numbers
# ---------------------------------------------------------------------------

def _build_tsma_row_map():
    row_map = {}
    r = 12
    for bge in BGE_A_LABELS:
        rows_for_bge = TSMA_BGE_ROWS[bge]
        row_map[bge] = {}
        for label, rtype in rows_for_bge:
            row_map[bge][rtype] = r
            r += 1
    assert r == 86, f"Expected TSMA TOTAL at row 86, got {r}"
    return row_map, r


TSMA_ROW_MAP, _TSMA_TOTAL_START = _build_tsma_row_map()

ROW_TSMA_TOTAL_CEL = 86
ROW_TSMA_TOTAL_MMS = 87
ROW_TSMA_TOTAL_DAT = 88
ROW_TSMA_TOTAL_VOI = 89
ROW_TSMA_TOTAL_OOS = 90

ROW_TSMA_SUM_CEL = 5
ROW_TSMA_SUM_DAT = 6
ROW_TSMA_SUM_VOI = 7
ROW_TSMA_SUM_OOS = 8
ROW_TSMA_SUM_TOT = 9
ROW_TSMA_SUM_MMS = 10

# ---------------------------------------------------------------------------
# Aggregate row lists
# ---------------------------------------------------------------------------

def _tsma_rows_by_type(rtype):
    return [TSMA_ROW_MAP[b][rtype] for b in BGE_A_LABELS if rtype in TSMA_ROW_MAP[b]]


TSMA_CEL_ROWS = _tsma_rows_by_type('cellular')
TSMA_MMS_ROWS = _tsma_rows_by_type('mms')
TSMA_DAT_ROWS = _tsma_rows_by_type('data')
TSMA_VOI_ROWS = _tsma_rows_by_type('voice') + _tsma_rows_by_type('voice_ivr')
TSMA_OOS_ROWS = _tsma_rows_by_type('oos')

# ---------------------------------------------------------------------------
# TSMA Lite row constants
# ---------------------------------------------------------------------------
ROW_TSMALITE_CONF    = 387
ROW_TSMALITE_LDIST   = 388
ROW_TSMALITE_VOICE   = 389
ROW_TSMALITE_CELL    = 390
ROW_TSMALITE_TOTAL   = 391
ROW_TSMALITE_VOICE2  = 393
ROW_TSMALITE_CELL2   = 394


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build():
    wb = xlsxwriter.Workbook(OUTPUT_PATH)
    ws = wb.add_worksheet("Sheet1")
    ws.outline_settings(True, False, True, True)
    tsma_data = load_tsma_data()
    tsma_lite_data = load_tsma_lite_data()

    F = _FmtCache(wb)

    f_bold    = F(bold=True)          # used for year/quarter header labels – no currency
    f_total   = F.n(bold=True)        # used for total rows that contain numbers
    f_section = F(bold=True)          # used for section name labels only

    set_column_widths(ws)

    # =========================================================
    # ROWS 1-3: Year / Quarter headers
    # =========================================================
    write_year_quarter_headers(ws, F)

    # =========================================================
    # ROW 4: Month labels  +  TSMA section header
    # =========================================================
    _fth   = F.n(bg_color=BG_TSMA_HDR)
    _fth_b = F.n(bold=True, bg_color=BG_TSMA_HDR)
    set_row_props(ws, 4, height=17, fmt=_fth)
    write(ws, 4, COL_B, "TSMA", _fth_b)
    write_month_label_row(ws, 4, _fth)

    # =========================================================
    # ROWS 5-10: TSMA summary rows
    # =========================================================
    for r in range(5, 11):
        set_row_props(ws, r, height=17, fmt=_fth)

    write(ws, 5, COL_B, "Cellular (incl. MMS)", _fth)
    write_monthly_sum_rows(ws, 5, [ROW_TSMA_TOTAL_CEL, ROW_TSMA_TOTAL_MMS], _fth)
    write_summary_cols(ws, 5, "Cellular (incl. MMS)")

    write(ws, 6, COL_B, "Data", _fth)
    write_monthly_ref(ws, 6, ROW_TSMA_TOTAL_DAT, _fth)
    write_summary_cols(ws, 6, "Data")

    write(ws, 7, COL_B, "Voice", _fth)
    write_monthly_ref(ws, 7, ROW_TSMA_TOTAL_VOI, _fth)
    write_summary_cols(ws, 7, "Voice")

    write(ws, 8, COL_B, "Out of Scope", _fth)
    write_monthly_ref(ws, 8, ROW_TSMA_TOTAL_OOS, _fth)

    _fth_tot = F.n(bold=True, bg_color=BG_TSMA_HDR)
    write(ws, 9, COL_B, "Total", _fth_tot)
    write_monthly_sum_range(ws, 9, 5, 8, _fth_tot)

    write(ws, 10, COL_B, "MMS", _fth)
    write_monthly_ref(ws, 10, ROW_TSMA_TOTAL_MMS, _fth)
    write_summary_cols(ws, 10, "MMS")

    # =========================================================
    # ROW 11-90: TSMA BGE detail  (outline level 1)
    # =========================================================
    _ftb     = F.n(bg_color=BG_TSMA_BGE)
    _ftb_b   = F.n(bold=True, bg_color=BG_TSMA_BGE)
    _ftb_ivr = F.n(bg_color=BG_IVR)

    set_row_props(ws, 11, fmt=_fth, opts={"level": 1})
    write(ws, 11, COL_A, "BGEs", _fth_b)

    for bge_name, a_label, a2_label in zip(BGES, BGE_A_LABELS, BGE_A2_LABELS):
        rows_def    = TSMA_BGE_ROWS[bge_name if bge_name != "VCHA\n(+PHC)" else "VCHA"]
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
            if rtype != "total":
                write_tsma_detail_row(ws, r, row_bg, tsma_data, a_label, rtype)
            if rtype == "total":
                write_monthly_sum_range(ws, r, first_r, last_r - 1, _ftb_b)

    # TSMA TOTAL aggregate rows 86-90
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
    _fcomb = F.n(bg_color=BG_COMBINED)
    set_row_props(ws, 91, height=16, fmt=_fcomb)
    write(ws, 91, 13, "TSMA+NGTAs", _fcomb)
    write_monthly_formula(
        ws, 91,
        lambda c: f"={col_letter(c)}{ROW_TSMA_SUM_TOT}"
                  f"+{col_letter(c)}116"   # TELUS NGTA summary Total (first_row=110 → row 116)
                  f"+{col_letter(c)}238",  # Rogers NGTA summary Total
        _fcomb,
    )

    # =========================================================
    # ROWS 92-108: Hidden TSMA sub-aggregate rows
    # =========================================================
    _hidden = {"hidden": True}

    gov_r = TSMA_ROW_MAP["Gov BC"]
    ecc_r = TSMA_ROW_MAP["ECC"]
    for r, label, r1, r2 in [
        (92, "Cellular", gov_r["cellular"], ecc_r["cellular"]),
        (93, "Data",     gov_r["data"],     ecc_r["data"]),
        (94, "Voice",    gov_r["voice"],    ecc_r["voice"]),
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

    health_bges = ["FHA","NHA","ICBC","PHSA","IHA","VIHA","FNHA","VCHA"]
    _hcel = [TSMA_ROW_MAP[b]["cellular"] for b in health_bges]
    _hmms = [TSMA_ROW_MAP[b]["mms"]      for b in ["FHA","PHSA","VCHA"]]
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

    # Separator row 109
    _fsep = F(bg_color=BG_SEPARATOR)
    set_row_props(ws, 109, height=16, fmt=_fsep)

    # =========================================================
    # ROWS 110-231: TELUS NGTA section  (delegated to telus_ngta.py)
    # =========================================================
    telus_data = load_telus_ngta()
    build_telus_ngta_section(ws, F, telus_data, first_row=110, include_separator=True)

    # =========================================================
    # ROWS 232-354: Rogers NGTA section  (delegated to rogers_ngta.py)
    # =========================================================
    rogers_data = load_rogers_ngta()
    build_rogers_ngta_section(ws, F, rogers_data, first_row=232, include_separator=True)

    # =========================================================
    # ROWS 355-385: Out of Scope section  (delegated to tsma_other.py)
    # =========================================================
    oos_data = load_tsma_other()
    build_oos_section(ws, F, oos_data, first_row=355)

    _fnum = F.n()   # plain currency format for TSMA Lite input rows
    _fnum_bold = F.n(bold=True)

    # =========================================================
    # ROWS 386-394: TSMA Lite  (quarterly data)
    # =========================================================
    set_row_props(ws, 386, height=16)
    write(ws, 386, COL_B, "TSMA Lite", f_section)

    for r, label in [
        (ROW_TSMALITE_CONF,  "Conferencing"),
        (ROW_TSMALITE_LDIST, "Long Distance"),
        (ROW_TSMALITE_VOICE, "Voice"),
        (ROW_TSMALITE_CELL,  "Cellular"),
    ]:
        set_row_props(ws, r, height=17, fmt=_fnum)
        write(ws, r, COL_B, label)

    for row_num, row_type in [
        (ROW_TSMALITE_CONF, "conferencing"),
        (ROW_TSMALITE_LDIST, "long_distance"),
        (ROW_TSMALITE_VOICE, "voice"),
        (ROW_TSMALITE_CELL, "cellular"),
    ]:
        for col in MONTH_COLS:
            amount = tsma_lite_data.get((row_type, col))
            if amount is not None:
                ws.write_number(row_num - 1, col, round(amount, 2), _fnum)

    set_row_props(ws, ROW_TSMALITE_TOTAL, height=17, fmt=_fnum_bold)
    write(ws, ROW_TSMALITE_TOTAL, COL_B, "Total", _fnum_bold)
    for col in MONTH_COLS:
        write_f(ws, ROW_TSMALITE_TOTAL, col,
                sum_range(ROW_TSMALITE_CONF, ROW_TSMALITE_CELL, col), _fnum_bold)

    set_row_props(ws, 392, height=17)

    set_row_props(ws, ROW_TSMALITE_VOICE2, height=17, fmt=_fnum_bold)
    write(ws, ROW_TSMALITE_VOICE2, COL_B, "Total Voice", _fnum_bold)
    for col in MONTH_COLS:
        cl = col_letter(col)
        write_f(ws, ROW_TSMALITE_VOICE2, col,
                f"={cl}{ROW_TSMALITE_CONF}+{cl}{ROW_TSMALITE_LDIST}+{cl}{ROW_TSMALITE_VOICE}",
                _fnum_bold)

    set_row_props(ws, ROW_TSMALITE_CELL2, height=17, fmt=_fnum_bold)
    write(ws, ROW_TSMALITE_CELL2, COL_B, "Total Cellular", _fnum_bold)
    for col in MONTH_COLS:
        write_f(ws, ROW_TSMALITE_CELL2, col, ref_cell(ROW_TSMALITE_CELL, col), _fnum_bold)

    # =========================================================
    # Freeze first 4 rows and first 2 columns
    # =========================================================
    ws.freeze_panes(4, 2)

    wb.close()
    print(f"✓ Written → {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
