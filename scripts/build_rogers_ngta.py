#!/usr/bin/env python3
"""Generate a standalone Rogers NGTA spend workbook.

Produces rogers_ngta_spend.xlsx in the same scripts/ folder.
Reads spend data from scripts/source/rogers_ngta_spend.csv (if present).

Run:  python3 scripts/build_rogers_ngta.py
Output: scripts/rogers_ngta_spend.xlsx
"""

import xlsxwriter

from sheet_utils import (
    _FmtCache,
    set_column_widths, write_year_quarter_headers, write_month_label_row,
)
from rogers_ngta import load_rogers_ngta, build_rogers_ngta_section, OUTPUT_PATH


def build():
    wb = xlsxwriter.Workbook(OUTPUT_PATH)
    ws = wb.add_worksheet("Rogers NGTA")
    ws.outline_settings(True, False, True, True)

    F = _FmtCache(wb)

    set_column_widths(ws)
    write_year_quarter_headers(ws, F)
    write_month_label_row(ws, 4)

    rogers_data = load_rogers_ngta()
    build_rogers_ngta_section(ws, F, rogers_data, first_row=5, include_separator=False)

    ws.freeze_panes(4, 2)

    wb.close()
    print(f"✓ Written → {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
