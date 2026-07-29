"""
Business rules
--------------
- Voice - IVR / Hosted IVR / IVR is rolled into Voice.
- Out of Scope is excluded from consolidated reporting.
- Other is excluded from consolidated reporting.
- School Districts is normalized to SD.

How to use
----------
1. Put this script in the same folder as your latest dashboard workbook.
2. If needed, update SOURCE_FILE below to match the workbook filename.
3. Run:
      python update_bge_category_dashboard_full_with_dropdown_fixes.py
4. The output workbook is created with:
      _BGE_Category_Dashboard_Updated_Dropdowns_Fixed.xlsx
   appended to the source filename.
"""

from pathlib import Path
from collections import defaultdict
import re

from openpyxl import load_workbook
from openpyxl import chart
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter, quote_sheetname
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo
from copy import copy

# =====================================================================
# CONFIGURATION
# =====================================================================

SOURCE_FILE = "spend_tracking_2026_07_03_0826AM.xlsx"
OUTPUT_FILE  = "BGE__Dashboard_Report.xlsx"

TELUS_GREEN = "00B050"
ROGERS_RED = "FF0000"

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(color="FFFFFF", bold=True)
SUB_FILL = PatternFill("solid", fgColor="D9EAF7")
LIGHT_FILL = PatternFill("solid", fgColor="F7FBFF")
WHITE_FILL = PatternFill("solid", fgColor="FFFFFF")
WHITE_FONT = Font(color="FFFFFF")
THIN_BLUE = Side(style="thin", color="B7CEE8")
CURFMT = "$#,##0;[Red]($#,##0);-"

EXPECTED_BGES = [
    "BC Hydro", "BCLC", "ECC", "FHA", "FNHA", "Gov BC", "ICBC", "IHA",
    "NHA", "PHSA", "SD", "VCHA", "VIHA", "WSBC"
]


# =====================================================================
# BASIC HELPERS
# =====================================================================

def to_number(value):
    """Convert workbook values to float, treating blanks and Excel errors as 0."""
    try:
        if value is None or value == "":
            return 0.0
        if isinstance(value, str) and value.startswith("#"):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def norm_bge(name):
    """Normalize BGE names for dashboard dropdowns."""
    return "SD" if name == "School Districts" else name


def norm_text(value):
    return str(value or "").strip().lower()


def find_source_file():
    """Find the source workbook in the current directory."""
    src = Path(SOURCE_FILE)
    if src.exists():
        return src

    # Fallback: use the most recent dashboard workbook if SOURCE_FILE is not found.
    files = sorted(Path(".").glob("*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files:
        if "dashboard" in f.name.lower():
            return f

    raise FileNotFoundError(
        "Could not find the dashboard workbook. Put this script beside the workbook or update SOURCE_FILE."
    )


# =====================================================================
# SOURCE PARSING
# =====================================================================

def get_month_cols(ws):
    """Read all month columns from Sheet1 ."""
    months, cols = [], []
    pat = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec) \d{4}$")

    for c in range(1, ws.max_column + 1):
        v = ws.cell(4, c).value
        if isinstance(v, str) and pat.match(v.strip()):
            m = v.strip().replace("Sept", "Sep")
            months.append(m)
            cols.append(c)
           
    return months, cols


def classify(label, source):
    """Classify a row label into the dashboard category fields."""
    txt = norm_text(label)
    if not txt:
        return None

    # Business rule: exclude Out of Scope and Other from consolidated reporting.
    if txt.startswith("total") or "out of scope" in txt or txt == "other" or txt.startswith("other"):
        return None

    # TSMA and TSMA Lite fields.
    if source in ("TSMA", "TSMA Lite"):
        if "cellular" in txt or "mms" in txt:
            return "Cellular_TSMA"
        if "data" in txt:
            return "Data_TSMA"
        # Business rule: Voice - IVR rolls into Voice.
        if "voice" in txt or "ivr" in txt or "long distance" in txt or "conferencing" in txt:
            return "Voice_TSMA"
        return None

    # TELUS/Rogers NGTA fields.
    if "cellular h/w" in txt or "cellular hw" in txt or "h/w" in txt:
        return "Cellular_HW"
    if "cellular plan" in txt or "cellular plans" in txt or txt == "cellular" or "mms" in txt:
        return "Cellular_Plan"
    if "data" in txt:
        return "Data"
    if "voice" in txt or "ivr" in txt or "long distance" in txt or "conferencing" in txt:
        return "Voice"

    return None


def find_row_col_b(ws, text, start=1):
    for r in range(start, ws.max_row + 1):
        if str(ws.cell(r, 2).value).strip() == text:
            return r
    return None


def parse_rows(ws, start, end, source, month_cols):
    """Parse rows within a TSMA/TELUS/Rogers block."""
    rows = []
    current_bge = None

    for r in range(start, end):
        aval = ws.cell(r, 1).value
        bval = ws.cell(r, 2).value

        if aval is not None and str(aval).strip() not in ("", "BGEs"):
            av = str(aval).strip()
            # Keep current BGE for annotation rows such as (+PHC).
            if not (av.startswith("(+") and current_bge):
                current_bge = av

        if not current_bge:
            continue

        cat = classify(bval, source)
        if cat is None:
            continue

        vals = [to_number(ws.cell(r, c).value) for c in month_cols]
        rows.append((norm_bge(current_bge), source, cat, vals))

    return rows


def parse_tsma(ws, month_cols):
    """Parse the first TSMA block."""
    bge_row = None
    for r in range(1, ws.max_row + 1):
        if str(ws.cell(r, 1).value).strip() == "BGEs":
            bge_row = r
            break

    if not bge_row:
        return []

    end = ws.max_row + 1
    for r in range(bge_row + 1, ws.max_row + 1):
        b = ws.cell(r, 2).value
        if isinstance(b, str) and b.startswith("TOTAL "):
            end = r
            break

    return parse_rows(ws, bge_row + 1, end, "TSMA", month_cols)


def parse_provider(ws, provider, month_cols):
    """Parse a provider block, e.g. TELUS NGTA or Rogers NGTA."""
    start = find_row_col_b(ws, provider)
    if start is None:
        return []

    bge_row = None
    for r in range(start, ws.max_row + 1):
        if str(ws.cell(r, 1).value).strip() == "BGEs":
            bge_row = r
            break

    if bge_row is None:
        return []

    end = ws.max_row + 1
    for r in range(bge_row + 1, ws.max_row + 1):
        label = str(ws.cell(r, 2).value or "").strip()
        if label.startswith("TOTAL ") or label in ("Rogers NGTA", "Out of Scope", "TSMA Lite"):
            end = r
            break

    return parse_rows(ws, bge_row + 1, end, provider, month_cols)


def build_detail_data(src_ws):
    """Build detailed BGE/category data from Sheet1."""
    months, month_cols = get_month_cols(src_ws)

    fields = [
        "Cellular_TSMA", "Data_TSMA", "Voice_TSMA",
        "Plan_Telus", "Plan_Rogers",
        "HW_Telus", "HW_Rogers",
        "Data_Telus", "Data_Rogers",
        "Voice_Telus", "Voice_Rogers",
    ]

    agg = defaultdict(lambda: [0.0] * len(months))

    all_rows = []
    all_rows.extend(parse_tsma(src_ws, month_cols))
    all_rows.extend(parse_provider(src_ws, "TELUS NGTA", month_cols))
    all_rows.extend(parse_provider(src_ws, "Rogers NGTA", month_cols))

    for bge, source, cat, vals in all_rows:
        field = None

        if cat == "Cellular_TSMA":
            field = "Cellular_TSMA"
        elif cat == "Data_TSMA":
            field = "Data_TSMA"
        elif cat == "Voice_TSMA":
            field = "Voice_TSMA"
        elif cat == "Cellular_Plan" and source == "TELUS NGTA":
            field = "Plan_Telus"
        elif cat == "Cellular_Plan" and source == "Rogers NGTA":
            field = "Plan_Rogers"
        elif cat == "Cellular_HW" and source == "TELUS NGTA":
            field = "HW_Telus"
        elif cat == "Cellular_HW" and source == "Rogers NGTA":
            field = "HW_Rogers"
        elif cat == "Data" and source == "TELUS NGTA":
            field = "Data_Telus"
        elif cat == "Data" and source == "Rogers NGTA":
            field = "Data_Rogers"
        elif cat == "Voice" and source == "TELUS NGTA":
            field = "Voice_Telus"
        elif cat == "Voice" and source == "Rogers NGTA":
            field = "Voice_Rogers"

        if field:
            agg[(bge, field)] = [a + b for a, b in zip(agg[(bge, field)], vals)]

    return months, agg, fields


# =====================================================================
# BGE LIST AND DROPDOWN FIXES
# =====================================================================

def get_bges(wb, agg):
    """Get BGE list from BGE_List, falling back to parsed data."""
    if "BGE_List" in wb.sheetnames:
        vals = [wb["BGE_List"].cell(r, 1).value for r in range(2, wb["BGE_List"].max_row + 1)]
        vals = [str(v).strip() for v in vals if v]
        if vals:
            vals = [norm_bge(v) for v in vals]

            seen = set(vals)

            ordered = [b for b in EXPECTED_BGES if b in seen]

            extras = [b for b in vals if b not in EXPECTED_BGES]

            final_bges = ordered + extras

            if "All BGEs" not in final_bges:
               final_bges.insert(0, "All BGEs")

            return final_bges

    bges = sorted({k[0] for k in agg.keys()})

    order = [b for b in EXPECTED_BGES if b in bges]

    final_bges = order + [b for b in bges if b not in order]

    return ["All BGEs"] + final_bges


def rebuild_bge_list(wb, bges):
    """Rebuild BGE_List sheet with complete BGE list."""
    if "BGE_List" in wb.sheetnames:
        ws = wb["BGE_List"]
        ws.delete_rows(1, ws.max_row)
    else:
        ws = wb.create_sheet("BGE_List")

    ws.append(["BGE"])
    for b in bges:
        ws.append([b])

    ws["A1"].fill = HEADER_FILL
    ws["A1"].font = HEADER_FONT
    ws["A1"].alignment = Alignment(horizontal="center")
    ws.column_dimensions["A"].width = 22
    ws.sheet_state = "hidden"
    return ws


def repair_dashboard_dropdowns(wb, bges):
    """Repair BGE dropdowns in both dashboard sheets."""
    if "BGE_List" not in wb.sheetnames:
        rebuild_bge_list(wb, bges)

    formula = f"={quote_sheetname('BGE_List')}!$A$2:$A${len(bges)+1}"

    for sheet_name in ["BGE_Category_Dashboard"]:
        if sheet_name not in wb.sheetnames:
            continue

        ws = wb[sheet_name]
        try:
            ws.data_validations.dataValidation = []
        except Exception:
            pass

        dv = DataValidation(type="list", formula1=formula, allow_blank=False)
        dv.error = "Select a BGE from the list."
        dv.errorTitle = "Invalid BGE"
        dv.prompt = "Choose a BGE from the dropdown."
        dv.promptTitle = "Select BGE"
        ws.add_data_validation(dv)
        dv.add(ws["B2"])

        # Keep current selected BGE if valid, otherwise set Gov BC.
        current = ws["B2"].value
        if current not in bges:
            ws["B2"] = "Gov BC" if "Gov BC" in bges else bges[0]

        ws["B2"].fill = SUB_FILL
        ws["B2"].font = Font(bold=True, color="1F4E78")
        ws["B2"].alignment = Alignment(horizontal="center")


# =====================================================================
# HIDDEN DETAIL DATA SHEET
# =====================================================================

def ensure_data_sheet(wb, months, bges, agg, fields):
    """Create hidden BGE_Category_Detail_Data sheet used by dashboard formulas."""
    sheet_name = "BGE_Category_Detail_Data"
    if sheet_name in wb.sheetnames:
        del wb[sheet_name]

    ws = wb.create_sheet(sheet_name)
    headers = ["BGE", "MonthIndex", "Month"] + fields + ["Key"]
    ws.append(headers)

    for bge in bges:

        if bge == "All BGEs":
           continue

        for i, month in enumerate(months, start=1):
    
            row = [bge, i, month]
            for field in fields:
                row.append(agg.get((bge, field), [0.0] * len(months))[i - 1])
            row.append(f"{bge}|{i}")
            ws.append(row)
        print("Adding All BGEs rows...")
        print("Months:", len(months))
    # -------------------------------------------------
# All BGEs rollup rows
# -------------------------------------------------

    for i, month in enumerate(months, start=1):

        row = ["All BGEs", i, month]

        for field in fields:

          total = 0

          for bge in bges:

            if bge == "All BGEs":
                continue

            total += agg.get(
                (bge, field),
                [0.0] * len(months)
            )[i - 1]

          row.append(total)

        row.append(f"All BGEs|{i}")

        ws.append(row)

    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")

    for c in range(1, ws.max_column + 1):
        ws.column_dimensions[get_column_letter(c)].width = 18

    try:
        tab = Table(displayName="BGECategoryDetailDataTable", ref=f"A1:{get_column_letter(ws.max_column)}{ws.max_row}")
        tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True, showColumnStripes=False)
        ws.add_table(tab)
    except Exception:
        pass

    ws.sheet_state = "hidden"
    return ws


# =====================================================================
# BGE CATEGORY DASHBOARD REBUILD
# =====================================================================

def hide_helper_columns(ws, start_col, end_col):
    """Make helper columns practically invisible but still usable for charts."""
    for c in range(start_col, end_col + 1):
        col = get_column_letter(c)
        ws.column_dimensions[col].width = 0.1
        for cell in ws[col]:
            cell.font = WHITE_FONT
            cell.fill = WHITE_FILL


def rebuild_category_dashboard(wb, months, bges):
    """Rebuild BGE_Category_Dashboard with detailed table and stacked chart."""
    if "BGE_Category_Dashboard" in wb.sheetnames:
        idx = wb.sheetnames.index("BGE_Category_Dashboard")
        del wb["BGE_Category_Dashboard"]
        ws = wb.create_sheet("BGE_Category_Dashboard", idx)
    else:
        ws = wb.create_sheet("BGE_Category_Dashboard", 1)

    ws.sheet_view.showGridLines = False

    # Title and selector.
    ws["A1"] = "BGE Monthly Category Dashboard"
    ws["A1"].font = Font(bold=True, size=16, color="1F4E78")
    ws["A2"] = "Select BGE:"
    ws["A2"].font = Font(bold=True)
    ws["B2"] = "Gov BC" if "Gov BC" in bges else bges[0]
    ws["B2"].fill = SUB_FILL
    ws["B2"].font = Font(bold=True, color="1F4E78")
    ws["B2"].alignment = Alignment(horizontal="center")
    ws["D2"] = "Detailed monthly table and stacked category bars update from the selected BGE."
    ws["D2"].font = Font(italic=True, color="666666")

    # Dropdown validation.
    dv = DataValidation(type="list", formula1=f"={quote_sheetname('BGE_List')}!$A$2:$A${len(bges)+1}", allow_blank=False)
    ws.add_data_validation(dv)
    dv.add(ws["B2"])

    # Visible table headers.
    headers = [
        "Month",
        "Cellular (TSMA+TSMA Lite)",
        "Data (TSMA+TSMA Lite)",
        "Voice (TSMA+TSMA Lite)",
        "Cellular Plan (TELUS NGTA)",
        "Cellular Plan (Rogers NGTA)",
        "Total Cellular Plan",
        "Cellular H/W (TELUS NGTA)",
        "Cellular H/W (Rogers NGTA)",
        "Total Cellular H/W",
        "Data (TELUS NGTA)",
        "Data (Rogers NGTA)",
        "Total Data",
        "Voice (TELUS NGTA)",
        "Voice (Rogers NGTA)",
        "Total Voice",
    ]

    header_row = 4
    first_row = 5

    for c, h in enumerate(headers, start=1):
        cell = ws.cell(header_row, c)
        cell.value = h
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", wrap_text=True)

    # BGE_Category_Detail_Data columns:
    # A BGE, B MonthIndex, C Month,
    # D Cellular_TSMA, E Data_TSMA, F Voice_TSMA,
    # G Plan_Telus, H Plan_Rogers, I HW_Telus, J HW_Rogers,
    # K Data_Telus, L Data_Rogers, M Voice_Telus, N Voice_Rogers, O Key
    for i, _month in enumerate(months, start=1):
        r = first_row + i - 1
        key = f'$B$2&"|"&{i}'
        match = f'MATCH({key},BGE_Category_Detail_Data!$O:$O,0)'

        formulas = [
            f'=INDEX(BGE_Category_Detail_Data!$C:$C,{match})',
            f'=IF(INDEX(BGE_Category_Detail_Data!$D:$D,{match})=0,"-",INDEX(BGE_Category_Detail_Data!$D:$D,{match}))',
            f'=IF(INDEX(BGE_Category_Detail_Data!$E:$E,{match})=0,"-",INDEX(BGE_Category_Detail_Data!$E:$E,{match}))',
            f'=IF(INDEX(BGE_Category_Detail_Data!$F:$F,{match})=0,"-",INDEX(BGE_Category_Detail_Data!$F:$F,{match}))',
            f'=IF(INDEX(BGE_Category_Detail_Data!$G:$G,{match})=0,"-",INDEX(BGE_Category_Detail_Data!$G:$G,{match}))',
            f'=IF(INDEX(BGE_Category_Detail_Data!$H:$H,{match})=0,"-",INDEX(BGE_Category_Detail_Data!$H:$H,{match}))',
            f'=IF((INDEX(BGE_Category_Detail_Data!$G:$G,{match})+INDEX(BGE_Category_Detail_Data!$H:$H,{match}))=0,"-",INDEX(BGE_Category_Detail_Data!$G:$G,{match})+INDEX(BGE_Category_Detail_Data!$H:$H,{match}))',
            f'=IF(INDEX(BGE_Category_Detail_Data!$I:$I,{match})=0,"-",INDEX(BGE_Category_Detail_Data!$I:$I,{match}))',
            f'=IF(INDEX(BGE_Category_Detail_Data!$J:$J,{match})=0,"-",INDEX(BGE_Category_Detail_Data!$J:$J,{match}))',
            f'=IF((INDEX(BGE_Category_Detail_Data!$I:$I,{match})+INDEX(BGE_Category_Detail_Data!$J:$J,{match}))=0,"-",INDEX(BGE_Category_Detail_Data!$I:$I,{match})+INDEX(BGE_Category_Detail_Data!$J:$J,{match}))',
            f'=IF(INDEX(BGE_Category_Detail_Data!$K:$K,{match})=0,"-",INDEX(BGE_Category_Detail_Data!$K:$K,{match}))',
            f'=IF(INDEX(BGE_Category_Detail_Data!$L:$L,{match})=0,"-",INDEX(BGE_Category_Detail_Data!$L:$L,{match}))',
            f'=IF((INDEX(BGE_Category_Detail_Data!$E:$E,{match})+INDEX(BGE_Category_Detail_Data!$K:$K,{match})+INDEX(BGE_Category_Detail_Data!$L:$L,{match}))=0,"-",INDEX(BGE_Category_Detail_Data!$E:$E,{match})+INDEX(BGE_Category_Detail_Data!$K:$K,{match})+INDEX(BGE_Category_Detail_Data!$L:$L,{match}))',
            f'=IF(INDEX(BGE_Category_Detail_Data!$M:$M,{match})=0,"-",INDEX(BGE_Category_Detail_Data!$M:$M,{match}))',
            f'=IF(INDEX(BGE_Category_Detail_Data!$N:$N,{match})=0,"-",INDEX(BGE_Category_Detail_Data!$N:$N,{match}))',
            f'=IF((INDEX(BGE_Category_Detail_Data!$F:$F,{match})+INDEX(BGE_Category_Detail_Data!$M:$M,{match})+INDEX(BGE_Category_Detail_Data!$N:$N,{match}))=0,"-",INDEX(BGE_Category_Detail_Data!$F:$F,{match})+INDEX(BGE_Category_Detail_Data!$M:$M,{match})+INDEX(BGE_Category_Detail_Data!$N:$N,{match}))',
        ]

        for c, formula in enumerate(formulas, start=1):
            ws.cell(r, c).value = formula
            if c > 1:
                ws.cell(r, c).number_format = CURFMT

        if r % 2 == 0:
            for c in range(1, len(headers) + 1):
                ws.cell(r, c).fill = LIGHT_FILL

        for c in range(1, len(headers) + 1):
            ws.cell(r, c).border = Border(bottom=THIN_BLUE)

    widths = [14, 22, 22, 22, 22, 22, 18, 22, 22, 18, 18, 18, 16, 18, 18, 16]
    for c, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(c)].width = w

    helper_col = 18   # Column R

    headers = [
     "Month",
     "Cellular",
     "Data",
     "Voice",
     "Cellular Plan",
     "Cellular H/W"
    ]

    for c, h in enumerate(headers, start=helper_col):
       ws.cell(header_row, c).value = h

   
    for i, month in enumerate(months, start=1):

      source_row = first_row + i - 1
      r = source_row

      ws.cell(r, helper_col).value = f"=A{source_row}"

      # Cellular
      ws.cell(r, helper_col + 1).value = f"=IFERROR(B{source_row},0)"

    # Data
      ws.cell(r, helper_col + 2).value = f"=IFERROR(M{source_row},0)"

    # Voice
      ws.cell(r, helper_col + 3).value = f"=IFERROR(P{source_row},0)"

    # Cellular Plan
      ws.cell(r, helper_col + 4).value = f"=IFERROR(G{source_row},0)"

    # Cellular H/W
      ws.cell(r, helper_col + 5).value = f"=IFERROR(J{source_row},0)"
      
    helper_last_row = first_row + len(months) - 1
    data = Reference(
     ws,
     min_col=helper_col + 1,   # Cellular
     max_col=helper_col + 5,   # Voice
     min_row=header_row,
     max_row=helper_last_row
    )
    cats = Reference(
     ws,
     min_col=helper_col,
     min_row=first_row,
     max_row=helper_last_row
   )
    chart = BarChart()

    chart.type = "col"
    chart.grouping = "clustered"
    chart.gapWidth = 350
    chart.title = "Monthly Spend by Service Tower for Selected BGE"
    #chart.y_axis.title = "Spend ($)"
    #chart.x_axis.title = "Month"

    chart.height = 16
    chart.width = 34
    chart.x_axis.delete = False
    chart.y_axis.delete = False
    chart.add_data(
     data,
     titles_from_data=True
    )

    chart.set_categories(cats)

    colors = [
      "4472C4",  # Cellular
      "5B9BD5",  # Data
      "A5A5A5",  # Voice
      "ED7D31",  # Cellular Plan
      "70AD47",  # Cellular H/W
    ]

    for series, color in zip(chart.series, colors):

      series.graphicalProperties.solidFill = color
      series.graphicalProperties.line.solidFill = color

    # Use same color for negative values
      try:
        series.invertIfNegative = False
      except:
        pass

    hide_helper_columns(
     ws,
     helper_col,
     helper_col + 5
    ) 
    ws.add_chart(chart, "A45")

# ==================================================
# Provider Breakdown Table
# ==================================================

    provider_start_row = 90

    provider_start_row = 90

    provider_headers = [
     "Month",
     "Cellular (Telus)",
     "Data (Telus)",
     "Voice (Telus)",
     "Cellular Plan (Telus)",
     "Cellular H/W (Telus)",
     "Data (Rogers)",
     "Voice (Rogers)",
     "Cellular Plan (Rogers)",
     "Cellular H/W (Rogers)"
    ]

    for c, h in enumerate(provider_headers, start=1):

       cell = ws.cell(provider_start_row, c)

       cell.value = h
       cell.fill = HEADER_FILL
       cell.font = HEADER_FONT
       cell.alignment = Alignment(
         horizontal="center",
         wrap_text=True
       )

    for i, month in enumerate(months, start=1):

      source_row = first_row + i - 1

      r = provider_start_row + i


      ws.cell(r, 1).value = f"=A{source_row}"

      ws.cell(r, 2).value = (
        f"=IFERROR(B{source_row},0)"
      )
      ws.cell(r, 3).value = (
        f'=IFERROR(IF(C{source_row}="-",0,C{source_row}),0)'
        f'+IFERROR(IF(K{source_row}="-",0,K{source_row}),0)'
      )
      ws.cell(r, 4).value = (
        f'=IFERROR(IF(D{source_row}="-",0,D{source_row}),0)'
        f'+IFERROR(IF(N{source_row}="-",0,N{source_row}),0)'
      )

      ws.cell(r, 5).value = (
        f"=IFERROR(E{source_row},0)"
      )
      ws.cell(r, 6).value = (
        f"=IFERROR(H{source_row},0)"
      )
      ws.cell(r, 7).value = (
        f"=IFERROR(L{source_row},0)"
      )

      ws.cell(r, 8).value = (
        f"=IFERROR(O{source_row},0)"
      )
      ws.cell(r, 9).value = (
        f"=IFERROR(F{source_row},0)"
      )

      ws.cell(r, 10).value = (
        f"=IFERROR(I{source_row},0)"
      )
      for col in range(2, 11):
        ws.cell(r, col).number_format = CURFMT

    provider_widths = [
     14,
     18,
     18,
     18,
     18,
     18,
     18,
     18,
     18,
     18
   ]

    for c, w in enumerate(provider_widths, start=1):

      ws.column_dimensions[
        get_column_letter(c)
      ].width = max(
        ws.column_dimensions[
            get_column_letter(c)
        ].width,
        w
      )

    provider_last_row = provider_start_row + len(months)

    provider_chart = LineChart()

    provider_chart.title = (
    "Monthly Spend by Provider Service Category"
)

    #provider_chart.y_axis.title = "Spend ($)"
    #provider_chart.x_axis.title = "Month"
    provider_chart.x_axis.delete = False
    provider_chart.y_axis.delete = False
    provider_chart.height = 16
    provider_chart.width = 42

    provider_chart.title = (
      "Monthly Spend by Provider Service Category"
    )

    #provider_chart.y_axis.title = "Spend ($)"
    #provider_chart.x_axis.title = "Month"

    provider_chart.height = 16
    provider_chart.width = 50

   

    provider_data = Reference(
      ws,
      min_col=2,
      max_col=10,
      min_row=provider_start_row,
      max_row=provider_last_row
    )
    provider_cats = Reference(
      ws,
      min_col=1,
      min_row=provider_start_row + 1,
      max_row=provider_last_row
    )
    provider_chart.add_data(
      provider_data,
      titles_from_data=True
    )

    provider_chart.set_categories(
      provider_cats
    )
    provider_colors = [

      "00B050",  # Cellular Telus

      "70AD47",  # Data Telus

      "92D050",  # Voice Telus

      "548235",  # Plan Telus

      "A9D18E",  # HW Telus

      "FF0000",  # Data Rogers

      "C00000",  # Voice Rogers

      "FF6666",  # Plan Rogers

      "E06666",  # HW Rogers
   ]

    for series, color in zip(
      provider_chart.series,
      provider_colors
    ):
      series.graphicalProperties.line.solidFill = color

      try:
        series.marker.symbol = "circle"
        series.marker.size = 7
      except:
        pass

    

    ws.add_chart(
      provider_chart,
       "A130"
    )
    
    # Chart helper table begins after visible table.

  

    return ws
def build_all_bge_rollup(months, agg, bges):

    rollup = []

    for month_idx, month in enumerate(months):

        telus = 0
        rogers = 0

        for bge in bges:

            telus += agg.get((bge, "Cellular_TSMA"), [0]*len(months))[month_idx]
            telus += agg.get((bge, "Data_TSMA"), [0]*len(months))[month_idx]
            telus += agg.get((bge, "Voice_TSMA"), [0]*len(months))[month_idx]

            telus += agg.get((bge, "Plan_Telus"), [0]*len(months))[month_idx]
            telus += agg.get((bge, "HW_Telus"), [0]*len(months))[month_idx]
            telus += agg.get((bge, "Data_Telus"), [0]*len(months))[month_idx]
            telus += agg.get((bge, "Voice_Telus"), [0]*len(months))[month_idx]

            rogers += agg.get((bge, "Plan_Rogers"), [0]*len(months))[month_idx]
            rogers += agg.get((bge, "HW_Rogers"), [0]*len(months))[month_idx]
            rogers += agg.get((bge, "Data_Rogers"), [0]*len(months))[month_idx]
            rogers += agg.get((bge, "Voice_Rogers"), [0]*len(months))[month_idx]

        rollup.append({
            "Month": month,
            "Telus": telus,
            "Rogers": rogers,
            "Total": telus + rogers
        })

    return rollup


def add_all_bge_rollup_chart(wb, months, agg, bges):

    if "BGE_Dashboard" not in wb.sheetnames:
        return

    ws = wb["BGE_Dashboard"]

    rollup = build_all_bge_rollup(months, agg, bges)

    start_col = 2    # Column B
    start_row = 45
   
# Section titles

    ws["B42"] = (
     '=IF($B$2="All BGEs",'
     '"ALL BGEs Summary (Selected)",'
     '"All BGEs Combined")'
    )
    ws["B42"].font = Font(
      bold=True,
      size=14,
      color="1F4E78"
    )
    ws["B41"] = (
     '=IF($B$2="All BGEs",'
     '"Showing consolidated results for ALL BGEs",'
     '"" )'
    )

    ws["B41"].font = Font(
     bold=True,
     size=12,
     color="C00000"
    )
    ws["B43"] = (
     '=IF($B$2="All BGEs",'
     '"Use this section when All BGEs is selected",'
     '"" )'
    )

    ws["B43"].font = Font(
      bold=True,
      color="1F4E78"
    )
    ws["B44"] = "Monthly Rollup Totals"
    ws["B44"].font = Font(
       bold=True
    )
    ws.cell(start_row, start_col).value = "Month"
    ws.cell(start_row, start_col + 1).value = "Total"
    ws.cell(start_row, start_col + 2).value = "Telus"
    ws.cell(start_row, start_col + 3).value = "Rogers"

# Optional formatting
    for c in range(start_col, start_col + 4):
       cell = ws.cell(start_row, c)
       cell.fill = HEADER_FILL
       cell.font = HEADER_FONT

    row = start_row + 1

    for rec in rollup:

        ws.cell(row, start_col).value = rec["Month"]
        ws.cell(row, start_col + 1).value = rec["Total"]
        ws.cell(row, start_col + 2).value = rec["Telus"]
        ws.cell(row, start_col + 3).value = rec["Rogers"]

        row += 1

   # for col in range(start_col, start_col + 4):
    #    ws.column_dimensions[get_column_letter(col)].hidden = True

    chart = LineChart()

    chart.title = "All BGE Monthly Spend Trend"
    chart.height = 12
    chart.width = 24

    data = Reference(
         ws,
         min_col=start_col + 1,
         max_col=start_col + 3,
         min_row=start_row,
         max_row=row - 1
    )

    cats = Reference(
       ws,
       min_col=start_col,
       min_row=start_row + 1,
       max_row=row - 1
    )

    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)

    chart.series[0].graphicalProperties.line.solidFill = "4472C4"
    chart.series[1].graphicalProperties.line.solidFill = "00B050"
    chart.series[2].graphicalProperties.line.solidFill = "FF0000"


    chart_title_row = row + 3
    chart_row = row + 5

    #ws[f"B{chart_title_row}"] = "All BGE Monthly Spend Trend"
    ws[f"B{chart_title_row}"].font = Font(
       bold=True,
       size=12,
       color="1F4E78"
    )

    ws.add_chart(chart, "L45")

  

def build_all_bge_rollup(months, agg, bges):
    """
    Build monthly All-BGE rollup:

    Telus  = TSMA + TSMA Lite + TELUS NGTA
    Rogers = Rogers NGTA
    Total  = Telus + Rogers
    """

    rollup = []

    for month_idx, month in enumerate(months):

        telus = 0
        rogers = 0

        for bge in bges:

            telus += agg.get((bge, "Cellular_TSMA"), [0]*len(months))[month_idx]
            telus += agg.get((bge, "Data_TSMA"), [0]*len(months))[month_idx]
            telus += agg.get((bge, "Voice_TSMA"), [0]*len(months))[month_idx]

            telus += agg.get((bge, "Plan_Telus"), [0]*len(months))[month_idx]
            telus += agg.get((bge, "HW_Telus"), [0]*len(months))[month_idx]
            telus += agg.get((bge, "Data_Telus"), [0]*len(months))[month_idx]
            telus += agg.get((bge, "Voice_Telus"), [0]*len(months))[month_idx]

            rogers += agg.get((bge, "Plan_Rogers"), [0]*len(months))[month_idx]
            rogers += agg.get((bge, "HW_Rogers"), [0]*len(months))[month_idx]
            rogers += agg.get((bge, "Data_Rogers"), [0]*len(months))[month_idx]
            rogers += agg.get((bge, "Voice_Rogers"), [0]*len(months))[month_idx]

        rollup.append(
            {
                "Month": month,
                "Telus": telus,
                "Rogers": rogers,
                "Total": telus + rogers,
            }
        )

    return rollup

def rebuild_bge_dashboard(wb, months, bges):
    """
    Fully rebuild BGE_Dashboard from scratch.

    Layout:
    - B2 dropdown for selected BGE
    - Top table/chart: selected BGE monthly Total, Telus, Rogers
    - Bottom table/chart: All BGEs monthly rollup Total, Telus, Rogers

    If B2 = "All BGEs":
    - Top selected-BGE table/chart is blanked
    - Bottom All BGEs rollup table/chart remains visible
    """

    sheet_name = "BGE_Dashboard"

    if sheet_name in wb.sheetnames:
        idx = wb.sheetnames.index(sheet_name)
        del wb[sheet_name]
        ws = wb.create_sheet(sheet_name, idx)
    else:
        ws = wb.create_sheet(sheet_name, 0)

    ws.sheet_view.showGridLines = False

    # ------------------------------------------------------------
    # Title and dropdown
    # ------------------------------------------------------------

    ws["A1"] = "BGE Monthly Spend Dashboard"
    ws["A1"].font = Font(
        bold=True,
        size=16,
        color="1F4E78"
    )

    ws["A2"] = "Select BGE:"
    ws["A2"].font = Font(bold=True)

    ws["B2"] = "Gov BC"
    ws["B2"].fill = SUB_FILL
    ws["B2"].font = Font(
        bold=True,
        color="1F4E78"
    )
    ws["B2"].alignment = Alignment(horizontal="center")

    dashboard_bges = [
       b for b in bges
       if b != "All BGEs"
    ]

    dv = DataValidation(
        type="list",
        formula1='"' + ",".join(dashboard_bges) + '"',
        allow_blank=False
    )

    dv.error = "Select a BGE from the list."
    dv.errorTitle = "Invalid BGE"
    dv.prompt = "Choose a BGE from the dropdown."
    dv.promptTitle = "Select BGE"

    ws.add_data_validation(dv)
    dv.add(ws["B2"])

    # ------------------------------------------------------------
    # Section 1: selected BGE table
    # ------------------------------------------------------------

    ws["B4"] = (
        '=IF($B$2="All BGEs",'
        '"Selected BGE Trend - Hidden for All BGEs",'
        '"Selected BGE Monthly Spend Trend")'
    )
    ws["B4"].font = Font(
        bold=True,
        size=14,
        color="1F4E78"
    )

    ws["B5"] = (
        '=IF($B$2="All BGEs",'
        '"All BGEs selected - use the All BGEs Summary section below.",'
        '"" )'
    )
    ws["B5"].font = Font(
        bold=True,
        size=12,
        color="C00000"
    )

    selected_start_row = 7
    selected_start_col = 2

    selected_headers = [
        "Month",
        "Total",
        "Telus",
        "Rogers"
    ]

    for c, h in enumerate(selected_headers, start=selected_start_col):
        cell = ws.cell(selected_start_row, c)
        cell.value = h
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")

    # Detail data columns:
    # A BGE
    # B MonthIndex
    # C Month
    # D Cellular_TSMA
    # E Data_TSMA
    # F Voice_TSMA
    # G Plan_Telus
    # H Plan_Rogers
    # I HW_Telus
    # J HW_Rogers
    # K Data_Telus
    # L Data_Rogers
    # M Voice_Telus
    # N Voice_Rogers
    # O Key

    for i, month in enumerate(months, start=1):

        r = selected_start_row + i

        match = (
            f'MATCH($B$2&"|"&{i},'
            f'BGE_Category_Detail_Data!$O:$O,0)'
        )

        month_formula = (
            f'=IF($B$2="All BGEs","",'
            f'INDEX(BGE_Category_Detail_Data!$C:$C,{match}))'
        )

        telus_expr = (
            f'IFERROR(INDEX(BGE_Category_Detail_Data!$D:$D,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$E:$E,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$F:$F,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$G:$G,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$I:$I,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$K:$K,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$M:$M,{match}),0)'
        )

        rogers_expr = (
            f'IFERROR(INDEX(BGE_Category_Detail_Data!$H:$H,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$J:$J,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$L:$L,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$N:$N,{match}),0)'
        )

        total_expr = f'({telus_expr})+({rogers_expr})'

        ws.cell(r, selected_start_col).value = month_formula

        ws.cell(r, selected_start_col + 1).value = (
            f'=IF($B$2="All BGEs","",'
            f'IF(({total_expr})=0,"-",({total_expr})))'
        )

        ws.cell(r, selected_start_col + 2).value = (
            f'=IF($B$2="All BGEs","",'
            f'IF(({telus_expr})=0,"-",({telus_expr})))'
        )

        ws.cell(r, selected_start_col + 3).value = (
            f'=IF($B$2="All BGEs","",'
            f'IF(({rogers_expr})=0,"-",({rogers_expr})))'
        )

        for c in range(selected_start_col + 1, selected_start_col + 4):
            ws.cell(r, c).number_format = CURFMT

        if r % 2 == 0:
            for c in range(selected_start_col, selected_start_col + 4):
                ws.cell(r, c).fill = LIGHT_FILL

        for c in range(selected_start_col, selected_start_col + 4):
            ws.cell(r, c).border = Border(bottom=THIN_BLUE)

    selected_last_row = selected_start_row + len(months)

    # ------------------------------------------------------------
    # Chart 1: selected BGE trend
    # ------------------------------------------------------------

    selected_chart = LineChart()

    selected_chart.title = "Selected BGE Monthly Spend"
    #selected_chart.y_axis.title = "Spend ($)"
    #selected_chart.x_axis.title = "Month"
    selected_chart.height = 12
    selected_chart.width = 24
    selected_chart.x_axis.delete = False
    selected_chart.y_axis.delete = False
    selected_data = Reference(
        ws,
        min_col=selected_start_col + 1,
        max_col=selected_start_col + 3,
        min_row=selected_start_row,
        max_row=selected_last_row
    )

    selected_cats = Reference(
        ws,
        min_col=selected_start_col,
        min_row=selected_start_row + 1,
        max_row=selected_last_row
    )

    selected_chart.add_data(
        selected_data,
        titles_from_data=True
    )

    selected_chart.set_categories(selected_cats)

    if len(selected_chart.series) >= 1:
        selected_chart.series[0].graphicalProperties.line.solidFill = "4472C4"
    if len(selected_chart.series) >= 2:
        selected_chart.series[1].graphicalProperties.line.solidFill = TELUS_GREEN
    if len(selected_chart.series) >= 3:
        selected_chart.series[2].graphicalProperties.line.solidFill = ROGERS_RED

    ws.add_chart(selected_chart, "L7")

    # ------------------------------------------------------------
    # Section 2: All BGEs rollup table
    # ------------------------------------------------------------

    rollup_title_row = 55
    rollup_start_row = 58
    rollup_start_col = 2

    ws[f"B{rollup_title_row}"] = (
        '=IF($B$2="All BGEs",'
        '"All BGEs Summary (Selected)",'
        '"All BGEs Combined")'
    )
    ws[f"B{rollup_title_row}"].font = Font(
        bold=True,
        size=14,
        color="1F4E78"
    )

    ws["B41"] = (
        '=IF($B$2="All BGEs",'
        '"Showing consolidated results for ALL BGEs",'
        '"" )'
    )
    ws["B41"].font = Font(
        bold=True,
        size=12,
        color="C00000"
    )

    ws["B43"] = (
        '=IF($B$2="All BGEs",'
        '"Use this section when All BGEs is selected",'
        '"" )'
    )
    ws["B43"].font = Font(
        bold=True,
        color="1F4E78"
    )

    ws["B44"] = "Monthly Rollup Totals"
    ws["B44"].font = Font(bold=True)

    rollup_headers = [
        "Month",
        "Total",
        "Telus",
        "Rogers"
    ]

    for c, h in enumerate(rollup_headers, start=rollup_start_col):
        cell = ws.cell(rollup_start_row, c)
        cell.value = h
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")

    for i, month in enumerate(months, start=1):

        r = rollup_start_row + i

        match = (
            f'MATCH("All BGEs|"&{i},'
            f'BGE_Category_Detail_Data!$O:$O,0)'
        )

        month_formula = (
            f'=INDEX(BGE_Category_Detail_Data!$C:$C,{match})'
        )

        telus_expr = (
            f'IFERROR(INDEX(BGE_Category_Detail_Data!$D:$D,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$E:$E,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$F:$F,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$G:$G,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$I:$I,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$K:$K,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$M:$M,{match}),0)'
        )

        rogers_expr = (
            f'IFERROR(INDEX(BGE_Category_Detail_Data!$H:$H,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$J:$J,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$L:$L,{match}),0)'
            f'+IFERROR(INDEX(BGE_Category_Detail_Data!$N:$N,{match}),0)'
        )

        total_expr = f'({telus_expr})+({rogers_expr})'

        ws.cell(r, rollup_start_col).value = month_formula
        ws.cell(r, rollup_start_col + 1).value = (
            f'=IF(({total_expr})=0,"-",({total_expr}))'
        )
        ws.cell(r, rollup_start_col + 2).value = (
            f'=IF(({telus_expr})=0,"-",({telus_expr}))'
        )
        ws.cell(r, rollup_start_col + 3).value = (
            f'=IF(({rogers_expr})=0,"-",({rogers_expr}))'
        )

        for c in range(rollup_start_col + 1, rollup_start_col + 4):
            ws.cell(r, c).number_format = CURFMT

        if r % 2 == 0:
            for c in range(rollup_start_col, rollup_start_col + 4):
                ws.cell(r, c).fill = LIGHT_FILL

        for c in range(rollup_start_col, rollup_start_col + 4):
            ws.cell(r, c).border = Border(bottom=THIN_BLUE)

    rollup_last_row = rollup_start_row + len(months)

    # ------------------------------------------------------------
    # Chart 2: All BGEs rollup trend
    # ------------------------------------------------------------

    rollup_chart = LineChart()

    rollup_chart.title = "All BGEs Monthly Spend"
    #rollup_chart.y_axis.title = "Spend ($)"
    #rollup_chart.x_axis.title = "Month"
    rollup_chart.height = 12
    rollup_chart.width = 24
    rollup_chart.x_axis.delete = False
    rollup_chart.y_axis.delete = False
    rollup_data = Reference(
        ws,
        min_col=rollup_start_col + 1,
        max_col=rollup_start_col + 3,
        min_row=rollup_start_row,
        max_row=rollup_last_row
    )

    rollup_cats = Reference(
        ws,
        min_col=rollup_start_col,
        min_row=rollup_start_row + 1,
        max_row=rollup_last_row
    )

    rollup_chart.add_data(
        rollup_data,
        titles_from_data=True
    )

    rollup_chart.set_categories(rollup_cats)

    if len(rollup_chart.series) >= 1:
        rollup_chart.series[0].graphicalProperties.line.solidFill = "4472C4"
    if len(rollup_chart.series) >= 2:
        rollup_chart.series[1].graphicalProperties.line.solidFill = TELUS_GREEN
    if len(rollup_chart.series) >= 3:
        rollup_chart.series[2].graphicalProperties.line.solidFill = ROGERS_RED

    ws.add_chart(rollup_chart, "L58")

    # ------------------------------------------------------------
    # Final formatting
    # ------------------------------------------------------------

    widths = {
        "A": 4,
        "B": 14,
        "C": 16,
        "D": 16,
        "E": 16,
        "L": 14,
        "M": 14,
        "N": 14,
        "O": 14,
    }

    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    ws.freeze_panes = "A7"

    return ws

# =====================================================================
# README UPDATE
# =====================================================================
def rebuild_govbc_stacked_bar_charts(wb, months):
    """
    Fully rebuild GovBC_Stacked_bar_charts from scratch.

    This sheet contains three Gov BC-only sections:
    1. Cellular table and charts
    2. Data table and chart
    3. Voice table and chart

    Source:
    BGE_Category_Detail_Data, where BGE = Gov BC.
    """

    sheet_name = "GovBC_Stacked_bar_charts"

    if sheet_name in wb.sheetnames:
        idx = wb.sheetnames.index(sheet_name)
        del wb[sheet_name]
        ws = wb.create_sheet(sheet_name, idx)
    else:
        ws = wb.create_sheet(sheet_name)

    ws.sheet_view.showGridLines = False

    bge_name = "Gov BC"

    # ------------------------------------------------------------
    # Title
    # ------------------------------------------------------------

    ws["A1"] = "Gov BC Stacked Bar Charts"
    ws["A1"].font = Font(
        bold=True,
        size=16,
        color="1F4E78"
    )

    ws["A2"] = "Source: Sheet1 -> BGE_Category_Detail_Data -> Gov BC only"
    ws["A2"].font = Font(
        italic=True,
        color="666666"
    )

    # ============================================================
    # SECTION 1: CELLULAR
    # ============================================================

    cellular_header_row = 4
    cellular_first_row = cellular_header_row + 1

    ws["A3"] = "Gov BC Cellular Monthly Spend"
    ws["A3"].font = Font(
        bold=True,
        size=14,
        color="1F4E78"
    )

    cellular_headers = [
        "Month",
        "Cellular (TSMA+TSMA Lite)",
        "TELUS NGTA (Cellular Plan)",
        "TELUS NGTA (Cellular H/W)",
        "Rogers NGTA (Cellular Plan)",
        "Rogers NGTA (Cellular H/W)"
    ]

    for c, h in enumerate(cellular_headers, start=1):
        cell = ws.cell(cellular_header_row, c)
        cell.value = h
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(
            horizontal="center",
            wrap_text=True
        )

    for i, month in enumerate(months, start=1):

        r = cellular_first_row + i - 1

        match = (
            f'MATCH("{bge_name}|"&{i},'
            f'BGE_Category_Detail_Data!$O:$O,0)'
        )

        # Columns in BGE_Category_Detail_Data:
        # C Month
        # D Cellular_TSMA
        # G Plan_Telus
        # H Plan_Rogers
        # I HW_Telus
        # J HW_Rogers

        ws.cell(r, 1).value = (
            f'=INDEX(BGE_Category_Detail_Data!$C:$C,{match})'
        )

        ws.cell(r, 2).value = (
            f'=IFERROR(INDEX(BGE_Category_Detail_Data!$D:$D,{match}),0)'
        )

        ws.cell(r, 3).value = (
            f'=IFERROR(INDEX(BGE_Category_Detail_Data!$G:$G,{match}),0)'
        )

        ws.cell(r, 4).value = (
            f'=IFERROR(INDEX(BGE_Category_Detail_Data!$I:$I,{match}),0)'
        )

        ws.cell(r, 5).value = (
            f'=IFERROR(INDEX(BGE_Category_Detail_Data!$H:$H,{match}),0)'
        )

        ws.cell(r, 6).value = (
            f'=IFERROR(INDEX(BGE_Category_Detail_Data!$J:$J,{match}),0)'
        )

        for c in range(2, 7):
            ws.cell(r, c).number_format = CURFMT

        if r % 2 == 0:
            for c in range(1, 7):
                ws.cell(r, c).fill = LIGHT_FILL

        for c in range(1, 7):
            ws.cell(r, c).border = Border(bottom=THIN_BLUE)

    cellular_last_row = cellular_first_row + len(months) - 1

    # ------------------------------------------------------------
    # Cellular helper table for stacked bar chart
    # Cellular Plan = Cellular TSMA + TELUS Plan + Rogers Plan
    # Cellular H/W  = TELUS H/W + Rogers H/W
    # ------------------------------------------------------------

    cellular_helper_col = 18  # R

    cellular_helper_headers = [
        "Month",
        "Cellular Plan",
        "Cellular H/W"
    ]

    for c, h in enumerate(cellular_helper_headers, start=cellular_helper_col):
        ws.cell(cellular_header_row, c).value = h

    for i, month in enumerate(months, start=1):

        source_row = cellular_first_row + i - 1
        r = source_row

        ws.cell(r, cellular_helper_col).value = f"=A{source_row}"

        # Cellular Plan total
        ws.cell(r, cellular_helper_col + 1).value = (
            f"=IFERROR(B{source_row},0)"
            f"+IFERROR(C{source_row},0)"
            f"+IFERROR(E{source_row},0)"
        )

        # Cellular H/W total
        ws.cell(r, cellular_helper_col + 2).value = (
            f"=IFERROR(D{source_row},0)"
            f"+IFERROR(F{source_row},0)"
        )

        ws.cell(r, cellular_helper_col + 1).number_format = CURFMT
        ws.cell(r, cellular_helper_col + 2).number_format = CURFMT

    # ------------------------------------------------------------
    # Cellular chart A: stacked bar chart
    # ------------------------------------------------------------

    cellular_stack_chart = BarChart()

    cellular_stack_chart.type = "col"
    cellular_stack_chart.grouping = "stacked"
    cellular_stack_chart.overlap = 100
    cellular_stack_chart.gapWidth = 250

    cellular_stack_chart.title = "Gov BC Cellular Monthly Spend - Plan vs H/W"
    #cellular_stack_chart.y_axis.title = "Spend ($)"
    #cellular_stack_chart.x_axis.title = "Month"
     
    cellular_stack_chart.height = 12
    cellular_stack_chart.width = 28
    cellular_stack_chart.x_axis.delete = False
    cellular_stack_chart.y_axis.delete = False
    cellular_stack_data = Reference(
        ws,
        min_col=cellular_helper_col + 1,
        max_col=cellular_helper_col + 2,
        min_row=cellular_header_row,
        max_row=cellular_last_row
    )

    cellular_stack_cats = Reference(
        ws,
        min_col=cellular_helper_col,
        min_row=cellular_first_row,
        max_row=cellular_last_row
    )

    cellular_stack_chart.add_data(
        cellular_stack_data,
        titles_from_data=True
    )

    cellular_stack_chart.set_categories(
        cellular_stack_cats
    )

    if len(cellular_stack_chart.series) >= 1:
        cellular_stack_chart.series[0].graphicalProperties.solidFill = "4472C4"
        cellular_stack_chart.series[0].graphicalProperties.line.solidFill = "4472C4"

    if len(cellular_stack_chart.series) >= 2:
        cellular_stack_chart.series[1].graphicalProperties.solidFill = "ED7D31"
        cellular_stack_chart.series[1].graphicalProperties.line.solidFill = "ED7D31"

    for s in cellular_stack_chart.series:
        try:
            s.invertIfNegative = False
        except:
            pass

    ws.add_chart(cellular_stack_chart, "I4")

    # ------------------------------------------------------------
    # Cellular chart B: line chart by component
    # ------------------------------------------------------------

    cellular_line_chart = LineChart()

    cellular_line_chart.title = "Gov BC Cellular Component Trend"
    #cellular_line_chart.y_axis.title = "Spend ($)"
    #cellular_line_chart.x_axis.title = "Month"

    cellular_line_chart.height = 12
    cellular_line_chart.width = 28
    cellular_line_chart.x_axis.delete = False
    cellular_line_chart.y_axis.delete = False
    cellular_line_data = Reference(
        ws,
        min_col=2,
        max_col=6,
        min_row=cellular_header_row,
        max_row=cellular_last_row
    )

    cellular_line_cats = Reference(
        ws,
        min_col=1,
        min_row=cellular_first_row,
        max_row=cellular_last_row
    )

    cellular_line_chart.add_data(
        cellular_line_data,
        titles_from_data=True
    )

    cellular_line_chart.set_categories(
        cellular_line_cats
    )

    line_colors = [
        "4472C4",
        "00B050",
        "70AD47",
        "FF0000",
        "C00000"
    ]

    for series, color in zip(cellular_line_chart.series, line_colors):
        series.graphicalProperties.line.solidFill = color

    ws.add_chart(cellular_line_chart, "I28")

    # ============================================================
    # SECTION 2: DATA
    # ============================================================

    data_header_row = cellular_last_row + 18
    data_first_row = data_header_row + 1

    ws.cell(data_header_row - 1, 1).value = "Gov BC Data Monthly Spend"
    ws.cell(data_header_row - 1, 1).font = Font(
        bold=True,
        size=14,
        color="1F4E78"
    )

    data_headers = [
        "Month",
        "Data (TSMA+TSMA Lite)",
        "Data (TELUS NGTA)",
        "Data (Rogers NGTA)"
    ]

    for c, h in enumerate(data_headers, start=1):
        cell = ws.cell(data_header_row, c)
        cell.value = h
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(
            horizontal="center",
            wrap_text=True
        )

    for i, month in enumerate(months, start=1):

        r = data_first_row + i - 1

        match = (
            f'MATCH("{bge_name}|"&{i},'
            f'BGE_Category_Detail_Data!$O:$O,0)'
        )

        # E Data_TSMA, K Data_Telus, L Data_Rogers

        ws.cell(r, 1).value = (
            f'=INDEX(BGE_Category_Detail_Data!$C:$C,{match})'
        )

        ws.cell(r, 2).value = (
            f'=IFERROR(INDEX(BGE_Category_Detail_Data!$E:$E,{match}),0)'
        )

        ws.cell(r, 3).value = (
            f'=IFERROR(INDEX(BGE_Category_Detail_Data!$K:$K,{match}),0)'
        )

        ws.cell(r, 4).value = (
            f'=IFERROR(INDEX(BGE_Category_Detail_Data!$L:$L,{match}),0)'
        )

        for c in range(2, 5):
            ws.cell(r, c).number_format = CURFMT

        if r % 2 == 0:
            for c in range(1, 5):
                ws.cell(r, c).fill = LIGHT_FILL

        for c in range(1, 5):
            ws.cell(r, c).border = Border(bottom=THIN_BLUE)

    data_last_row = data_first_row + len(months) - 1

    # Data helper for Telus/Rogers stacked chart

    data_helper_col = 22  # V

    ws.cell(data_header_row, data_helper_col).value = "Month"
    ws.cell(data_header_row, data_helper_col + 1).value = "Telus"
    ws.cell(data_header_row, data_helper_col + 2).value = "Rogers"

    for i, month in enumerate(months, start=1):

        source_row = data_first_row + i - 1
        r = source_row

        ws.cell(r, data_helper_col).value = f"=A{source_row}"

        # Telus = Data TSMA + Data TELUS NGTA
        ws.cell(r, data_helper_col + 1).value = (
            f"=IFERROR(B{source_row},0)"
            f"+IFERROR(C{source_row},0)"
        )

        # Rogers = Data Rogers NGTA
        ws.cell(r, data_helper_col + 2).value = (
            f"=IFERROR(D{source_row},0)"
        )

        ws.cell(r, data_helper_col + 1).number_format = CURFMT
        ws.cell(r, data_helper_col + 2).number_format = CURFMT

    data_chart = BarChart()

    data_chart.type = "col"
    data_chart.grouping = "stacked"
    data_chart.overlap = 100
    data_chart.gapWidth = 250

    data_chart.title = "Gov BC Data Monthly Spend - Telus vs Rogers"
    #data_chart.y_axis.title = "Spend ($)"
    #data_chart.x_axis.title = "Month"

    data_chart.height = 12
    data_chart.width = 28
    data_chart.x_axis.delete = False
    data_chart.y_axis.delete = False
    data_chart_data = Reference(
        ws,
        min_col=data_helper_col + 1,
        max_col=data_helper_col + 2,
        min_row=data_header_row,
        max_row=data_last_row
    )

    data_chart_cats = Reference(
        ws,
        min_col=data_helper_col,
        min_row=data_first_row,
        max_row=data_last_row
    )

    data_chart.add_data(
        data_chart_data,
        titles_from_data=True
    )

    data_chart.set_categories(
        data_chart_cats
    )

    if len(data_chart.series) >= 1:
        data_chart.series[0].graphicalProperties.solidFill = TELUS_GREEN
        data_chart.series[0].graphicalProperties.line.solidFill = TELUS_GREEN

    if len(data_chart.series) >= 2:
        data_chart.series[1].graphicalProperties.solidFill = ROGERS_RED
        data_chart.series[1].graphicalProperties.line.solidFill = ROGERS_RED

    for s in data_chart.series:
        try:
            s.invertIfNegative = False
        except:
            pass

    ws.add_chart(data_chart, f"I{data_header_row}")

    # ============================================================
    # SECTION 3: VOICE
    # ============================================================

    voice_header_row = data_last_row + 18
    voice_first_row = voice_header_row + 1

    ws.cell(voice_header_row - 1, 1).value = "Gov BC Voice Monthly Spend"
    ws.cell(voice_header_row - 1, 1).font = Font(
        bold=True,
        size=14,
        color="1F4E78"
    )

    voice_headers = [
        "Month",
        "Voice (TSMA+TSMA Lite)",
        "Voice (TELUS NGTA)",
        "Voice (Rogers NGTA)"
    ]

    for c, h in enumerate(voice_headers, start=1):
        cell = ws.cell(voice_header_row, c)
        cell.value = h
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(
            horizontal="center",
            wrap_text=True
        )

    for i, month in enumerate(months, start=1):

        r = voice_first_row + i - 1

        match = (
            f'MATCH("{bge_name}|"&{i},'
            f'BGE_Category_Detail_Data!$O:$O,0)'
        )

        # F Voice_TSMA, M Voice_Telus, N Voice_Rogers

        ws.cell(r, 1).value = (
            f'=INDEX(BGE_Category_Detail_Data!$C:$C,{match})'
        )

        ws.cell(r, 2).value = (
            f'=IFERROR(INDEX(BGE_Category_Detail_Data!$F:$F,{match}),0)'
        )

        ws.cell(r, 3).value = (
            f'=IFERROR(INDEX(BGE_Category_Detail_Data!$M:$M,{match}),0)'
        )

        ws.cell(r, 4).value = (
            f'=IFERROR(INDEX(BGE_Category_Detail_Data!$N:$N,{match}),0)'
        )

        for c in range(2, 5):
            ws.cell(r, c).number_format = CURFMT

        if r % 2 == 0:
            for c in range(1, 5):
                ws.cell(r, c).fill = LIGHT_FILL

        for c in range(1, 5):
            ws.cell(r, c).border = Border(bottom=THIN_BLUE)

    voice_last_row = voice_first_row + len(months) - 1

    # Voice helper for Telus/Rogers stacked chart

    voice_helper_col = 26  # Z

    ws.cell(voice_header_row, voice_helper_col).value = "Month"
    ws.cell(voice_header_row, voice_helper_col + 1).value = "Telus"
    ws.cell(voice_header_row, voice_helper_col + 2).value = "Rogers"

    for i, month in enumerate(months, start=1):

        source_row = voice_first_row + i - 1
        r = source_row

        ws.cell(r, voice_helper_col).value = f"=A{source_row}"

        # Telus = Voice TSMA + Voice TELUS NGTA
        ws.cell(r, voice_helper_col + 1).value = (
            f"=IFERROR(B{source_row},0)"
            f"+IFERROR(C{source_row},0)"
        )

        # Rogers = Voice Rogers NGTA
        ws.cell(r, voice_helper_col + 2).value = (
            f"=IFERROR(D{source_row},0)"
        )

        ws.cell(r, voice_helper_col + 1).number_format = CURFMT
        ws.cell(r, voice_helper_col + 2).number_format = CURFMT

    voice_chart = BarChart()

    voice_chart.type = "col"
    voice_chart.grouping = "stacked"
    voice_chart.overlap = 100
    voice_chart.gapWidth = 250

    voice_chart.title = "Gov BC Voice Monthly Spend - Telus vs Rogers"
    #voice_chart.y_axis.title = "Spend ($)"
    #voice_chart.x_axis.title = "Month"

    voice_chart.height = 12
    voice_chart.width = 28
    voice_chart.x_axis.delete = False
    voice_chart.y_axis.delete = False
    voice_chart_data = Reference(
        ws,
        min_col=voice_helper_col + 1,
        max_col=voice_helper_col + 2,
        min_row=voice_header_row,
        max_row=voice_last_row
    )

    voice_chart_cats = Reference(
        ws,
        min_col=voice_helper_col,
        min_row=voice_first_row,
        max_row=voice_last_row
    )

    voice_chart.add_data(
        voice_chart_data,
        titles_from_data=True
    )

    voice_chart.set_categories(
        voice_chart_cats
    )

    if len(voice_chart.series) >= 1:
        voice_chart.series[0].graphicalProperties.solidFill = TELUS_GREEN
        voice_chart.series[0].graphicalProperties.line.solidFill = TELUS_GREEN

    if len(voice_chart.series) >= 2:
        voice_chart.series[1].graphicalProperties.solidFill = ROGERS_RED
        voice_chart.series[1].graphicalProperties.line.solidFill = ROGERS_RED

    for s in voice_chart.series:
        try:
            s.invertIfNegative = False
        except:
            pass

    ws.add_chart(voice_chart, f"I{voice_header_row}")

    # ------------------------------------------------------------
    # Hide helper columns
    # ------------------------------------------------------------

    hide_helper_columns(ws, cellular_helper_col, cellular_helper_col + 2)
    hide_helper_columns(ws, data_helper_col, data_helper_col + 2)
    hide_helper_columns(ws, voice_helper_col, voice_helper_col + 2)

    # ------------------------------------------------------------
    # Widths and final formatting
    # ------------------------------------------------------------

    widths = {
        "A": 14,
        "B": 22,
        "C": 22,
        "D": 22,
        "E": 24,
        "F": 24,
        "I": 16,
        "J": 16,
        "K": 16,
        "L": 16,
        "M": 16,
        "N": 16,
        "O": 16,
    }

    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    ws.freeze_panes = "A5"

    return ws


# =====================================================================
# README UPDATE
# =====================================================================

def update_readme(wb):
    if "README_BGE_Dashboard" not in wb.sheetnames:
        return

    ws = wb["README_BGE_Dashboard"]
    row = ws.max_row + 1
    ws.cell(row, 1).value = "BGE category dashboard TSMA Data/Voice update"
    ws.cell(row, 2).value = (
        "BGE_Category_Dashboard now includes Data (TSMA+TSMA Lite) and Voice (TSMA+TSMA Lite) "
        "after Cellular (TSMA+TSMA Lite). The chart shows five category bars beside each other "
        "for each month and stacks each bar by Telus in green and Rogers in red. For Data and Voice "
        "bars, the Telus stack equals TSMA+TSMA Lite plus TELUS NGTA; Rogers equals Rogers NGTA. "
        "BGE_Dashboard and BGE_Category_Dashboard dropdowns were repaired. Out of Scope remains "
        "excluded and Voice - IVR remains rolled into Voice."
    )


# =====================================================================
# MAIN
# =====================================================================

def main():
    src = find_source_file()
    out = src.with_name(OUTPUT_FILE)

    from openpyxl import Workbook

    wb = load_workbook(src)

    if "Sheet1" not in wb.sheetnames:
      raise ValueError(
        "Sheet1 not found. Cannot rebuild detailed BGE category dashboard."
    )



    # Use data_only copy for source values.
    wb_values = load_workbook(src, data_only=True)
    months, agg, fields = build_detail_data(wb_values["Sheet1"])

    bges = get_bges(wb, agg)

    for sheet_name in [
      "BGE_List",
      "BGE_Category_Detail_Data",
      "BGE_Dashboard",
      "BGE_Category_Dashboard",
      "GovBC_Stacked_bar_charts"
   ]:
      if sheet_name in wb.sheetnames:
        del wb[sheet_name]


    rebuild_bge_list(wb, bges)

    ensure_data_sheet(
      wb,
      months,
      bges,
      agg,
      fields
    )

    rebuild_govbc_stacked_bar_charts(
      wb,
      months
    )

    rebuild_bge_dashboard(
      wb,
      months,
      bges
    )

    rebuild_category_dashboard(
      wb,
      months,
      bges
)
    #add_all_bge_rollup_chart(
    # wb,
    # months,
    # agg,
    # bges
    #)
    # Critical fix: restore dropdowns in BOTH dashboard sheets.
    repair_dashboard_dropdowns(wb, bges)

    update_readme(wb)

    wb.active = wb.sheetnames.index("BGE_Category_Dashboard")
    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    wb.calculation.calcMode = "auto"
    sheet1 = wb["Sheet1"]

    wb._sheets.remove(sheet1)
    wb._sheets.insert(0, sheet1)
    wb.save(out)

    print(f"Created: {out}")
    print(f"BGEs: {len(bges)}; months: {len(months)} ({months[0]} to {months[-1]})")
    print("Updated BGE_Category_Dashboard table/chart and repaired dropdowns in both dashboard sheets.")


if __name__ == "__main__":
    main()
