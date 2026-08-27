import pandas as pd
import re
import os

from report_writer import write_price_validation_workbook

# =========================
# File paths
# =========================

DATA_DIR = "."

price_xlsx = os.path.join(DATA_DIR, "cellular.xlsx")
report_xlsx = os.path.join(
    DATA_DIR,
    "2026_06_BC Gov't NGTA - Administrator Reports_Usage_&_Spend.xlsx"
)
output_file = os.path.join(DATA_DIR, "Wireless_Service_ID_Comparison_Rate.xlsx")


# =========================
# Load source files
# =========================

price = pd.read_excel(price_xlsx, engine="openpyxl")
report = pd.read_excel(
    report_xlsx,
    dtype=str,
    engine="openpyxl"
)

# Clean column names
price.columns = [str(c).strip() for c in price.columns]
report.columns = [str(c).strip() for c in report.columns]


# =========================
# Helper functions
# =========================

def find_col(columns, options):
    """
    Robustly find a column by comparing simplified column names.
    """
    normalized = {
        re.sub(r"[^a-z0-9]", "", c.lower()): c
        for c in columns
    }

    for option in options:
        key = re.sub(r"[^a-z0-9]", "", option.lower())
        if key in normalized:
            return normalized[key]

    for c in columns:
        c_lower = c.lower()
        if any(option.lower() in c_lower for option in options):
            return c

    raise KeyError(f"Missing column among: {options}")


def normalize_service_id(value):
    """
    Normalize Service IDs.

    Example:
    CVDULTDM -> CVDULTD
    """
    if pd.isna(value):
        return ""

    service_id = str(value).strip()

    # Normalize monthly variant IDs, e.g. CVDULTDM -> CVDULTD
    if service_id.endswith("M") and len(service_id) > 1:
        return service_id[:-1]

    return service_id


def parse_money(value):
    """
    Extract numeric amount from fee text.

    Examples:
    "$7.49 per seat" -> 7.49
    "$12.00" -> 12.00
    "No Charge" -> 0.00
    "($10.00)" -> -10.00
    "-10.00" -> -10.00
    """
    if pd.isna(value):
        return None

    text = str(value).strip()

    if not text:
        return None

    lower_text = text.lower()

    if "no charge" in lower_text:
        return 0.0

    if lower_text in {"n/a", "na", "none"}:
        return None

    # Remove commas and dollar signs from values like $1,996.00
    text = text.replace(",", "").replace("$", "")

    # Handle accounting-style negatives: ($12.34)
    is_parentheses_negative = text.startswith("(") and text.endswith(")")
    text = text.replace("(", "").replace(")", "")

    match = re.search(r"[-+]?\s*([0-9]+(?:\.[0-9]+)?)", text)

    if match:
        amount = float(match.group(1))
        if text.strip().startswith("-") or is_parentheses_negative:
            amount = -amount
        return amount

    return None


# =========================
# Identify required columns
# =========================

price_service_id_col = find_col(price.columns, ["Service ID"])
price_fee_col = find_col(price.columns, ["Monthly Fixed Fee"])

report_service_id_col = find_col(report.columns, ["SERVICE_ID", "Service ID"])
report_billed_col = find_col(
    report.columns,
    ["BILLED_AMOUNT(PRE-TAX)", "BILLED_AMOUNT(PRE TAX)", "Billed Amount Pre Tax"]
)


# =========================
# Prepare Price Book data
# =========================

price["Normalized Service ID"] = price[price_service_id_col].map(normalize_service_id)
price["Monthly Fixed Fee Numeric"] = price[price_fee_col].map(parse_money)

price_clean = price[
    price["Normalized Service ID"].astype(str).str.strip().ne("")
].copy()

price_clean = (
    price_clean[
        [
            price_service_id_col,
            "Normalized Service ID",
            price_fee_col,
            "Monthly Fixed Fee Numeric",
        ]
    ]
    .drop_duplicates("Normalized Service ID", keep="first")
)


# =========================
# Prepare Monthly Report data
# =========================

report["Billed Amount Numeric"] = report[report_billed_col].map(parse_money)

# Remove all report rows where BILLED AMOUNT(PRE TAX) is exactly zero.
# Rows with blank or non-numeric billed amount are kept for review.
zero_billed_count = int(report["Billed Amount Numeric"].eq(0).sum())
report_nonzero = report[report["Billed Amount Numeric"].ne(0)].copy()

# Capture report rows with blank SERVICE_ID after removing zero-billed rows.
blank_service_id_mask = (
    report_nonzero[report_service_id_col].isna()
    | report_nonzero[report_service_id_col].astype(str).str.strip().eq("")
)

missing_service_id_report = report_nonzero[blank_service_id_mask].copy()

# Put helper columns near the front for easier review in the Missing Service ID sheet.
missing_service_id_front_cols = [report_service_id_col, report_billed_col, "Billed Amount Numeric"]
missing_service_id_columns = (
    missing_service_id_front_cols
    + [c for c in missing_service_id_report.columns if c not in missing_service_id_front_cols]
)
missing_service_id_report = missing_service_id_report[missing_service_id_columns]

# Exclude blank SERVICE_ID rows from price-book comparison.
report_for_comparison = report_nonzero[~blank_service_id_mask].copy()

report_for_comparison["Normalized Service ID"] = report_for_comparison[
    report_service_id_col
].map(normalize_service_id)

# Keep ONLY required monthly report columns for comparison.
monthly_report_clean = report_for_comparison[
    [
        report_service_id_col,
        "Normalized Service ID",
        "Billed Amount Numeric",
        "MSF_OTHER_OPTIONS",
        "HARDWARE",
        "OTHERS",
    ]
].copy()

monthly_report_clean.rename(
    columns={
        report_service_id_col: "Monthly Report Service ID",
        "Billed Amount Numeric": "Billed Amount (Rate)",
    },
    inplace=True
)


# =========================
# Build comparison table
# =========================

comparison = monthly_report_clean.merge(
    price_clean[
        [
            price_service_id_col,
            "Normalized Service ID",
            "Monthly Fixed Fee Numeric",
        ]
    ],
    on="Normalized Service ID",
    how="left"
)

comparison.rename(
    columns={
        price_service_id_col: "Price Book Service ID",
        "Monthly Fixed Fee Numeric": "Monthly Fixed Fee (from the Price Book)",
    },
    inplace=True
)

# Add Match Status
comparison["Match Status (Service ID)"] = comparison["Price Book Service ID"].apply(
    lambda x: "Matched" if pd.notna(x) else "Missing from Price Book"
)

# Add difference column. The Excel formula is added later when writing each row.
comparison["Difference (Billed Amount - Monthly Fixed Fee)"] = (
    comparison["Billed Amount (Rate)"]
    - comparison["Monthly Fixed Fee (from the Price Book)"]
)

# Sort output
status_order = {
    "Missing Service ID from Report": 0,
    "Missing from Price Book": 2,
    "Matched": 1,
}
comparison["__sort_order"] = (
    comparison["Match Status (Service ID)"]
    .map(status_order)
    .fillna(9)
)

comparison = (
    comparison
    .sort_values("__sort_order")
    .drop(columns="__sort_order")
)

comparison_desired_order = [
    "Price Book Service ID",
    "Monthly Report Service ID",
    "Match Status (Service ID)",
    "Monthly Fixed Fee (from the Price Book)",
    "Billed Amount (Rate)",
    "MSF_OTHER_OPTIONS",
    "HARDWARE",
    "OTHERS",
    "Difference (Billed Amount - Monthly Fixed Fee)",
]

comparison_columns = [
    col for col in comparison_desired_order
    if col in comparison.columns
]

comparison = comparison[comparison_columns]

mismatched_rate = comparison[
    (
        comparison["Match Status (Service ID)"] == "Matched"
    )
    &
    (
        comparison["Difference (Billed Amount - Monthly Fixed Fee)"]
        .abs() > 0.005
    )
].copy()

# Add Missing Service ID rows to Complete Comparison

missing_service_comparison = pd.DataFrame({
    "Price Book Service ID": None,
    "Monthly Report Service ID": missing_service_id_report[report_service_id_col],
    "Match Status (Service ID)": "Missing Service ID from Report",
    "Monthly Fixed Fee (from the Price Book)": None,
    "Billed Amount (Rate)": missing_service_id_report["Billed Amount Numeric"],
    "MSF_OTHER_OPTIONS": missing_service_id_report["MSF_OTHER_OPTIONS"],
    "HARDWARE": missing_service_id_report["HARDWARE"],
    "OTHERS": missing_service_id_report["OTHERS"],
    "Difference (Billed Amount - Monthly Fixed Fee)": None
})
comparison = pd.concat(
    [
        comparison,
        missing_service_comparison
    ],
    ignore_index=True
)


# =========================
# Save workbook
# (styling lives in report_writer.py, shared with main.py / RUNBOOK.ipynb)
# =========================

summary_rows = [
    (
        "Matched Service IDs",
        len(comparison[comparison["Match Status (Service ID)"] == "Matched"]),
    ),
    (
        "Missing from Price Book",
        len(comparison[comparison["Match Status (Service ID)"] == "Missing from Price Book"]),
    ),
    (
        "Missing Service ID from Report",
        len(missing_service_id_report),
    ),
    (
        "Mismatched Rate",
        len(mismatched_rate),
    ),
    (
        "Rows removed because billed amount is zero",
        zero_billed_count,
    ),
    ("Total comparison rows", len(comparison)),
]

write_price_validation_workbook(
    comparison,
    summary_rows,
    output_file,
    missing_service_id_df=missing_service_id_report,
)

print(f"Created: {output_file}")
print(f"Total rows: {len(comparison)}")
print("Matched:", len(comparison[comparison["Match Status (Service ID)"] == "Matched"]))
print("Missing from Price Book:", len(comparison[comparison["Match Status (Service ID)"] == "Missing from Price Book"]))
print("Missing Service ID:", len(missing_service_id_report))
print("Rows removed because billed amount is zero:", zero_billed_count)
