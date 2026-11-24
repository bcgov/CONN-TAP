"""
Builds the Rogers CSA spend files from the BGE / Sub-BGE reference data in the database.

1. docs/templates/CSA_Spend_TEMPLATE.xlsx - the template for a new master file:
     - a blank month sheet (named YYYY-MM) with one row per BGE / Sub-BGE
     - "BGE List", our BGE and Sub-BGE codes
2. docs/templates/CSA_BGE_List.xlsx - only the "BGE List" sheet. When BGEs / Sub-BGEs change,
   the master file's owner clears its "BGE List" sheet and pastes this one over it.
   The month sheets are not touched.

Connection: env DATABASE_URL, else the local docker database.

Usage:
    python scripts/templates/build_csa_template.py              # both files
    python scripts/templates/build_csa_template.py --bge-list   # only the BGE list
"""
import os
import sys
from datetime import date
from pathlib import Path

import psycopg
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.properties import Outline

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DSN = "postgresql://app:app@localhost:5432/app"
OUTPUT_DIR = REPO_ROOT / "docs" / "templates"
TEMPLATE_FILE = OUTPUT_DIR / "CSA_Spend_TEMPLATE.xlsx"
BGE_LIST_FILE = OUTPUT_DIR / "CSA_BGE_List.xlsx"

AUTHOR = "Telecom Access Point Portal Team"
MONTH_SHEET_NAME = date.today().strftime("%Y-%m")  # the month the template is built in
FORMULA_ROWS = 200      # rows that get the Post-Tax formula
VALIDATION_ROWS = 5000  # rows that get the dropdowns and number checks

FONT_NAME = "Arial"
MONEY_FORMAT = '$#,##0.00;($#,##0.00);"-"'
LIGHT_BLUE = PatternFill("solid", fgColor="D9E1F2")
DARK_BLUE = PatternFill("solid", fgColor="B4C6E7")
NAVY = PatternFill("solid", fgColor="1F3864")
GREY_LINE = Side(style="thin", color="BFBFBF")
BORDER = Border(left=GREY_LINE, right=GREY_LINE, top=GREY_LINE, bottom=GREY_LINE)

# Column names follow the CSA report.
COLUMNS = [
    "BGE",
    "Sub-BGE",
    "SAF AMOUNT",
    "911 MSF",
    "MSF Voice Plan",
    "VOICE PLAN OVERAGE CHARGE",
    "VOICE PLAN CDN LD CHARGES",
    "LD US",
    "LD Intl",
    "VOICE PLAN US + INT ROAM MIN CHARGES",
    "VOICE PLAN INT'L ROAM MIN CHARGES",
    "VOICE PLAN DACC CHARGES",
    "SMS MSG OVERAGE CHARGES",
    "VOICE PLAN OTHER CHARGES",
    "VOICE PLAN TOTAL CHARGES",
    "DATA PLAN MSF",
    "Data Overage",
    "DATA PLAN OTHER CHARGES",
    "DATA PLAN TOTAL CHARGES",
    "Hardware",
    "Billed Amount (Pre-Tax)",
    "HST",
    "PST",
    "GST",
    "QST",
    "Billed Amount (Post-Tax)",
]

# These headers get the darker blue.
KEY_COLUMNS = [
    "VOICE PLAN TOTAL CHARGES",
    "DATA PLAN TOTAL CHARGES",
    "Hardware",
    "Billed Amount (Pre-Tax)",
    "Billed Amount (Post-Tax)",
]


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

def load_bges(conn):
    """Returns a list of (code, name) from reference_data.bge."""
    rows = conn.execute("""
        select code, name
        from reference_data.bge
        order by id
    """).fetchall()
    return [(code, name) for code, name in rows]


def load_sub_bges(conn):
    """
    Returns a list of dicts from reference_data.sub_bge: code, name, bge and parent.
    parent is the Sub-BGE a designee sits under (e.g. Citizens Services), otherwise None.
    """
    rows = conn.execute("""
        select s.code, s.name, b.code as bge, p.code as parent
        from reference_data.sub_bge s
        join reference_data.bge b on b.id = s.bge_id
        left join reference_data.sub_bge p on p.id = s.parent_sub_bge_id
        order by s.id
    """).fetchall()
    return [
        {"code": code, "name": name, "bge": bge, "parent": parent}
        for code, name, bge, parent in rows
    ]


# ---------------------------------------------------------------------------
# Month sheet
# ---------------------------------------------------------------------------

def column_letter(column_name):
    return get_column_letter(COLUMNS.index(column_name) + 1)


def add_month_sheet(workbook, bge_count, sub_bge_count):
    sheet = workbook.create_sheet(MONTH_SHEET_NAME)

    # Headers
    for col, name in enumerate(COLUMNS, start=1):
        cell = sheet.cell(row=1, column=col, value=name)
        cell.font = Font(name=FONT_NAME, size=10, bold=True)
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        if name in KEY_COLUMNS:
            cell.fill = DARK_BLUE
        else:
            cell.fill = LIGHT_BLUE

        letter = get_column_letter(col)
        sheet.column_dimensions[letter].width = 13
        if name in ("BGE", "Sub-BGE"):
            sheet.column_dimensions[letter].number_format = "@"
        else:
            sheet.column_dimensions[letter].number_format = MONEY_FORMAT

    sheet.column_dimensions["A"].width = 14
    sheet.column_dimensions["B"].width = 44
    sheet.column_dimensions["C"].width = 15
    sheet.row_dimensions[1].height = 45
    sheet.freeze_panes = "C2"
    last_column = get_column_letter(len(COLUMNS))
    sheet.auto_filter.ref = f"A1:{last_column}1"

    # Post-Tax adds the four tax columns to Pre-Tax.
    pre_tax = column_letter("Billed Amount (Pre-Tax)")
    qst = column_letter("QST")
    post_tax_col = COLUMNS.index("Billed Amount (Post-Tax)") + 1
    for row in range(2, FORMULA_ROWS + 1):
        cell = sheet.cell(row=row, column=post_tax_col, value=f"=SUM({pre_tax}{row}:{qst}{row})")
        cell.font = Font(name=FONT_NAME, size=10)
        cell.number_format = MONEY_FORMAT

    # Dropdowns read the hidden code lists in columns E and F of the BGE List sheet.
    bge_dropdown = DataValidation(
        type="list",
        formula1=f"'BGE List'!$E$2:$E${bge_count + 1}",
        showErrorMessage=True,
        errorTitle="BGE",
        error="Use a BGE code from the 'BGE List' sheet.",
    )
    bge_dropdown.add(f"A2:A{VALIDATION_ROWS}")
    sheet.add_data_validation(bge_dropdown)

    sub_bge_dropdown = DataValidation(
        type="list",
        formula1=f"'BGE List'!$F$2:$F${sub_bge_count + 1}",
        allow_blank=True,
        showErrorMessage=True,
        errorTitle="Sub-BGE",
        error="Use a Sub-BGE code from the 'BGE List' sheet, or leave blank.",
    )
    sub_bge_dropdown.add(f"B2:B{VALIDATION_ROWS}")
    sheet.add_data_validation(sub_bge_dropdown)

    amount_check = DataValidation(
        type="decimal",
        operator="between",
        formula1="-100000000",
        formula2="1000000000",
        showErrorMessage=True,
        errorTitle="Amount",
        error="Enter a dollar amount (0 if none).",
    )
    amount_check.add(f"C2:{last_column}{VALIDATION_ROWS}")
    sheet.add_data_validation(amount_check)


# ---------------------------------------------------------------------------
# BGE List sheet
# ---------------------------------------------------------------------------

def write_bge_row(sheet, row, code, name):
    for col, value in enumerate([code, None, name], start=1):
        cell = sheet.cell(row=row, column=col, value=value)
        cell.font = Font(name=FONT_NAME, size=10, bold=True)
        cell.fill = LIGHT_BLUE
        cell.border = BORDER


def write_sub_bge_row(sheet, row, sub_bge, level):
    """level 1 = Sub-BGE under a BGE, level 2 = designee under a Sub-BGE."""
    for col, value in enumerate([sub_bge["bge"], sub_bge["code"], sub_bge["name"]], start=1):
        cell = sheet.cell(row=row, column=col, value=value)
        cell.border = BORDER
        if col == 1:
            cell.font = Font(name=FONT_NAME, size=10, color="808080")
        else:
            cell.font = Font(name=FONT_NAME, size=10, color="000000")

    sheet.cell(row=row, column=2).alignment = Alignment(indent=2 * (level - 1))
    sheet.cell(row=row, column=3).alignment = Alignment(indent=2 * level)
    sheet.row_dimensions[row].outlineLevel = level


def write_sub_bges_under(sheet, row, bge_code, sub_bges):
    """Writes a BGE's Sub-BGEs, each followed by its designees. Returns the next free row."""
    for sub_bge in sub_bges:
        if sub_bge["bge"] != bge_code or sub_bge["parent"]:
            continue
        write_sub_bge_row(sheet, row, sub_bge, level=1)
        row += 1

        for designee in sub_bges:
            if designee["parent"] == sub_bge["code"]:
                write_sub_bge_row(sheet, row, designee, level=2)
                row += 1
    return row


def add_bge_list_sheet(workbook, bges, sub_bges):
    """
    Lists each BGE, then its Sub-BGEs, then any designees under a Sub-BGE.
    Rows are grouped so each BGE can be collapsed in Excel.
    """
    sheet = workbook.create_sheet("BGE List")
    sheet.sheet_properties.outlinePr = Outline(summaryBelow=False)  # +/- button on the BGE row

    for col, header in enumerate(["BGE", "Sub-BGE", "Name"], start=1):
        cell = sheet.cell(row=1, column=col, value=header)
        cell.font = Font(name=FONT_NAME, size=10, bold=True, color="FFFFFF")
        cell.fill = NAVY
        cell.border = BORDER

    row = 2
    for bge_code, bge_name in bges:
        write_bge_row(sheet, row, bge_code, bge_name)
        row = write_sub_bges_under(sheet, row + 1, bge_code, sub_bges)

    sheet.column_dimensions["A"].width = 16
    sheet.column_dimensions["B"].width = 22
    sheet.column_dimensions["C"].width = 60
    sheet.freeze_panes = "A2"

    # Hidden code lists for the month sheet dropdowns.
    sheet.cell(row=1, column=5, value="BGE codes")
    sheet.cell(row=1, column=6, value="Sub-BGE codes")
    for i, (bge_code, _) in enumerate(bges, start=2):
        sheet.cell(row=i, column=5, value=bge_code)
    for i, sub_bge in enumerate(sub_bges, start=2):
        sheet.cell(row=i, column=6, value=sub_bge["code"])
    sheet.column_dimensions["E"].hidden = True
    sheet.column_dimensions["F"].hidden = True


def save_workbook(workbook, path, title):
    # Shown in Excel under File > Properties
    workbook.properties.creator = AUTHOR
    workbook.properties.lastModifiedBy = AUTHOR
    workbook.properties.title = title

    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)
    print(f"Saved {path.relative_to(REPO_ROOT)}")


def build_template(bges, sub_bges):
    workbook = Workbook()
    workbook.remove(workbook.active)
    add_month_sheet(workbook, len(bges), len(sub_bges))
    add_bge_list_sheet(workbook, bges, sub_bges)
    workbook.calculation.fullCalcOnLoad = True  # Excel calculates the Post-Tax formulas on open
    save_workbook(workbook, TEMPLATE_FILE, "CSA Spend Template")


def build_bge_list(bges, sub_bges):
    workbook = Workbook()
    workbook.remove(workbook.active)
    add_bge_list_sheet(workbook, bges, sub_bges)
    save_workbook(workbook, BGE_LIST_FILE, "CSA BGE List")


def main():
    with psycopg.connect(os.environ.get("DATABASE_URL", DEFAULT_DSN)) as conn:
        bges = load_bges(conn)
        sub_bges = load_sub_bges(conn)

    if "--bge-list" not in sys.argv:
        build_template(bges, sub_bges)
    build_bge_list(bges, sub_bges)


if __name__ == "__main__":
    main()
