#!/usr/bin/env python3
"""Generate a standalone Out-of-Scope spend workbook.

Produces tsma_other_spend.xlsx in the same scripts/ folder.
Reads spend data from scripts/source/tsma_other_spend.csv.

Row layout of the standalone file:
  Rows 1-3 : Year spans / Calendar quarters / Fiscal quarters
  Row 4    : Month labels (Jan 2024 … Dec 2026)
  Row 5    : "Out of Scope" section header  (first_row=5)
  Row 6    : "Managed Router" sub-header
  Rows 7-13 : Managed Router detail (7 orgs)
  Row 14   : Managed Router Total
  Row 15   : "Managed WLAN/Managed Wi-Fi" sub-header
  Rows 16-21: WLAN detail (6 orgs)
  Row 22   : WLAN Total
  Row 23   : "Managed Security/Managed Firewall" sub-header
  Rows 24-33: Security detail (10 orgs)
  Row 34   : Security Total
  Row 35   : blank

Run:  python3 scripts/build_tsma_other.py
Output: scripts/tsma_other_spend.xlsx
"""

import xlsxwriter

from sheet_utils import (
    _FmtCache,
    set_column_widths, write_year_quarter_headers, write_month_label_row,
)
from tsma_other import load_tsma_other, build_oos_section, OUTPUT_PATH


def build():
    wb = xlsxwriter.Workbook(OUTPUT_PATH)
    ws = wb.add_worksheet("OOS")

    ws.outline_settings(True, False, True, True)

    F = _FmtCache(wb)

    set_column_widths(ws)

    # Rows 1-3: year spans, calendar quarters, fiscal quarters
    write_year_quarter_headers(ws, F)

    # Row 4: plain month labels
    write_month_label_row(ws, 4)

    # Rows 5-35: Out-of-Scope section
    oos_data = load_tsma_other()
    build_oos_section(ws, F, oos_data, first_row=5)

    ws.freeze_panes(4, 2)

    wb.close()
    print(f"✓ Written → {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
