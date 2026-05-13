"""Out-of-Scope section — CSV ingestion and worksheet section writer.

Covers the three sub-sections at the end of the spend report:
  • Managed Router
  • Managed WLAN / Managed Wi-Fi
  • Managed Security / Managed Firewall

Source CSV: scripts/source/tsma_other_spend.csv
  Columns:  feed, rcid_cust_nm, year_num, month_num, total_billed_amt
  feed values: managed_router | managed_wlan_wifi | managed_security

The section builder is parameterised by `first_row` so it can be embedded
in the full spend_tracking workbook (first_row=355) or generated as a
standalone file (first_row=5, after four rows of month/quarter headers).

Row layout relative to first_row
---------------------------------
  first_row + 0  : "Out of Scope" header
  first_row + 1  : "Managed Router" sub-header
  first_row + 2  : first Managed Router org row
  first_row + 8  : last  Managed Router org row  (7 orgs)
  first_row + 9  : Managed Router Total
  first_row + 10 : "Managed WLAN/Managed Wi-Fi" sub-header
  first_row + 11 : first WLAN org row
  first_row + 16 : last  WLAN org row  (6 orgs)
  first_row + 17 : WLAN Total
  first_row + 18 : "Managed Security/Managed Firewall" sub-header
  first_row + 19 : first Security org row
  first_row + 28 : last  Security org row  (10 orgs)
  first_row + 29 : Security Total  (SUM of rows +20 … +28; first org excluded, matching original)
  first_row + 30 : blank trailing row
"""

import csv
import os

from sheet_utils import (
    COL_B, COL_AO, COL_AP, COL_AQ, COL_AR, COL_AS,
    FIRST_MONTH, LAST_MONTH, MONTH_COLS,
    write, write_f, set_row_props,
    write_monthly_sum_range,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SOURCE_DIR  = os.path.join(os.path.dirname(__file__), "source")
TSMA_OTHER_CSV = os.path.join(SOURCE_DIR, "tsma_other_spend.csv")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "tsma_other_spend.xlsx")

# ---------------------------------------------------------------------------
# Organisation lists (define the row order in each sub-section)
# These names must match rcid_cust_nm values in the CSV exactly.
# ---------------------------------------------------------------------------
OOS_MR_ORGS = [
    "CHILDRENS & WOMENS HEALTH CENTRE OF BC SOCIETY",
    "FIRST NATIONS HEALTH AUTHORITY",
    "GBC - MINISTRY OF CITIZENS SERVICES",
    "GBC - SHARED SERVICES BC",
    "GBC - MINISTRY OF EDUCATION & CHILD CARE",
    "BRITISH COLUMBIA LIQUOR DISTRIBUTION BRANCH",
    "GBC - LIQUOR DISTRIBUTION BRANCH",
]

OOS_WLAN_ORGS = [
    "VANCOUVER COASTAL HEALTH AUTHORITY O/A OLIVE DEVAUD RESIDENCE",
    "VANCOUVER COASTAL HEALTH AUTHORITY O/A LIONS GATE HOSPITAL",
    "VANCOUVER COASTAL HEALTH AUTHORITY HOWE SOUND HOME SUPPORT SERVICES",
    "VANCOUVER COASTAL HEALTH AUTHORITY",
    "PROVINCIAL HEALTH SERVICES AUTHORITY",
    "GREATER VANCOUVER MENTAL HEALTH SERVICE",
]

OOS_SEC_ORGS = [
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

# Map feed column value → org list for that sub-section
_FEED_TO_ORGS = {
    "managed_router":    OOS_MR_ORGS,
    "managed_wlan_wifi": OOS_WLAN_ORGS,
    "managed_security":  OOS_SEC_ORGS,
}

# ---------------------------------------------------------------------------
# CSV ingestion
# ---------------------------------------------------------------------------

def load_tsma_other(path: str = TSMA_OTHER_CSV) -> dict:
    """Read tsma_other_spend.csv and return {(feed, org_name, col_idx): value}.

    Rows with year < 2024 or year > 2026 are silently skipped.
    Unknown feed values or org names that don't appear in any org list are
    also silently ignored so the sheet still builds with a partial CSV.
    """
    # Build a flat set of all org names that appear in any section for fast lookup
    all_orgs = {org for orgs in _FEED_TO_ORGS.values() for org in orgs}

    data: dict = {}
    if not os.path.exists(path):
        return data

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        reader.fieldnames = [h.strip().lower() for h in (reader.fieldnames or [])]
        for row in reader:
            try:
                year  = int(row.get("year_num",  0))
                month = int(row.get("month_num", 0))
            except (ValueError, TypeError):
                continue

            if year < 2024 or year > 2026:
                continue

            col = FIRST_MONTH + (year - 2024) * 12 + (month - 1)
            if not (FIRST_MONTH <= col <= LAST_MONTH):
                continue

            feed = row.get("feed", "").strip().lower()
            if feed not in _FEED_TO_ORGS:
                continue

            org = row.get("rcid_cust_nm", "").strip()
            if org not in all_orgs:
                continue

            raw = row.get("total_billed_amt", "").strip()
            if not raw:
                continue
            try:
                data[(feed, org, col)] = float(raw.replace(",", ""))
            except ValueError:
                pass

    return data


# ---------------------------------------------------------------------------
# Section builder
# ---------------------------------------------------------------------------

def build_oos_section(ws, F, oos_data: dict, *, first_row: int = 355) -> None:
    """Write the complete Out-of-Scope section to *ws* starting at *first_row*.

    Args:
        ws:        xlsxwriter Worksheet.
        F:         _FmtCache instance bound to the workbook.
        oos_data:  dict returned by load_tsma_other().
        first_row: Row number of the "Out of Scope" header (1-based).
                   Use 355 in the full spend_tracking sheet,
                   use 5 in the standalone tsma_other_spend sheet.
    """
    f_bold    = F(bold=True)
    f_section = F(bold=True)
    f_total   = F.n(bold=True)
    _fnum     = F.n()
    _collapsed = {"level": 1, "hidden": True}

    # ---- Derive all row positions ----
    mr_hdr    = first_row + 1
    mr_start  = first_row + 2
    mr_rows   = list(range(mr_start, mr_start + len(OOS_MR_ORGS)))
    mr_total  = mr_start + len(OOS_MR_ORGS)       # = first_row + 9

    wlan_hdr  = mr_total + 1                       # = first_row + 10
    wlan_start = wlan_hdr + 1                      # = first_row + 11
    wlan_rows = list(range(wlan_start, wlan_start + len(OOS_WLAN_ORGS)))
    wlan_total = wlan_start + len(OOS_WLAN_ORGS)  # = first_row + 17

    sec_hdr   = wlan_total + 1                     # = first_row + 18
    sec_start = sec_hdr + 1                        # = first_row + 19
    sec_rows  = list(range(sec_start, sec_start + len(OOS_SEC_ORGS)))
    sec_total = sec_start + len(OOS_SEC_ORGS)      # = first_row + 29

    # ---- Section header row ----
    set_row_props(ws, first_row, height=16)
    write(ws, first_row, COL_B, "Out of Scope", f_section)
    write(ws, first_row, COL_AO, 2024,      f_bold)
    write(ws, first_row, COL_AP, 2025,      f_bold)
    write(ws, first_row, COL_AQ, "Q1 2024", f_bold)
    write(ws, first_row, COL_AR, "Q1 2025", f_bold)
    write(ws, first_row, COL_AS, "Q4 2025", f_bold)

    def _write_subsection(sub_hdr_row, sub_label, feed_key, org_list, detail_rows,
                          total_row, sum_from_row):
        """Write one OOS sub-section (header + detail rows + total)."""
        set_row_props(ws, sub_hdr_row, height=16)
        write(ws, sub_hdr_row, COL_B, sub_label)
        if sub_hdr_row == mr_hdr:
            write(ws, sub_hdr_row, COL_AO, "Jan-Dec")

        for r, org in zip(detail_rows, org_list):
            set_row_props(ws, r, height=17, fmt=_fnum, opts=_collapsed)
            write(ws, r, COL_B, org)
            for col in MONTH_COLS:
                val = oos_data.get((feed_key, org, col))
                if val is not None:
                    write(ws, r, col, val, _fnum)

        set_row_props(ws, total_row, height=17, opts={"collapsed": True})
        write(ws, total_row, COL_B, "Total", f_total)
        write_monthly_sum_range(ws, total_row, sum_from_row, total_row - 1, f_total)

    # ---- Managed Router ----
    _write_subsection(
        mr_hdr, "Managed Router", "managed_router",
        OOS_MR_ORGS, mr_rows, mr_total, mr_start,
    )

    # ---- Managed WLAN / Managed Wi-Fi ----
    _write_subsection(
        wlan_hdr, "Managed WLAN/Managed Wi-Fi", "managed_wlan_wifi",
        OOS_WLAN_ORGS, wlan_rows, wlan_total, wlan_start,
    )

    # ---- Managed Security / Managed Firewall ----
    # Note: the total formula starts at sec_start + 1 (skips first org row),
    # matching the pattern in the original spreadsheet.
    _write_subsection(
        sec_hdr, "Managed Security/Managed Firewall", "managed_security",
        OOS_SEC_ORGS, sec_rows, sec_total, sec_start + 1,
    )

    # ---- Blank trailing row ----
    set_row_props(ws, sec_total + 1, height=16)
