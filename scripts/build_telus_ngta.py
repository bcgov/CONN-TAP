#!/usr/bin/env python3
"""Generate a standalone TELUS NGTA spend workbook.

Produces telus_ngta_spend.xlsx in the same scripts/ folder.
Reads spend data from scripts/source/telus_ngta_spend.csv (if present).

Row layout of the standalone file:
  Rows 1-3 : Year spans / Calendar quarters / Fiscal quarters
  Row 4    : Month labels (Jan 2024 … Dec 2026)
  Row 5    : TELUS NGTA section header  (first_row=5)
  Rows 6-10: Summary rows (Cellular Plans / H/W / Data / Voice / Other)
  Row 11   : Summary Total
  Row 12   : BGEs header
  Rows 13-96 : BGE detail (14 BGEs × 6 rows)
  Rows 97-101: Aggregate TOTAL rows
  Rows 102-126: Hidden sub-aggregate rows

Run:  python3 scripts/build_telus_ngta.py
Output: scripts/telus_ngta_spend.xlsx
"""

import xlsxwriter

from sheet_utils import (
    _FmtCache,
    set_column_widths, write_year_quarter_headers, write_month_label_row,
)
from telus_ngta import load_telus_ngta, build_telus_ngta_section, OUTPUT_PATH


def build():
    wb = xlsxwriter.Workbook(OUTPUT_PATH)
    ws = wb.add_worksheet("TELUS NGTA")

    # Outline: summary rows below detail, collapse buttons on right
    ws.outline_settings(True, False, True, True)

    F = _FmtCache(wb)

    set_column_widths(ws)

    # Rows 1-3: year spans, calendar quarters, fiscal quarters
    write_year_quarter_headers(ws, F)

    # Row 4: plain month labels (no section-header colour)
    write_month_label_row(ws, 4, F=F)

    # Rows 5-126: TELUS NGTA section (no trailing separator needed)
    telus_data = load_telus_ngta()
    build_telus_ngta_section(ws, F, telus_data, first_row=5, include_separator=False)

    # Freeze first 4 rows and first 2 columns (same as the full workbook)
    ws.freeze_panes(4, 2)

    wb.close()
    print(f"✓ Written → {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
