# main.py
# Entry point for the DB-sourced Rogers price validation export.
# Runs reporting.validate_rogers_cellular_prices() (defined in
# rogers_wireless_price_validation_function.sql) and writes the result to Excel.

import argparse
import os
import pandas as pd
from sqlalchemy import create_engine, text

from report_writer import write_price_validation_workbook

# ==============================
# CONFIG
# ==============================
parser = argparse.ArgumentParser(description="Rogers price validation export")
parser.add_argument(
    "--month",
    help="Billing month to filter to, format YYYY-MM (default: all months in the raw tables)",
)
args = parser.parse_args()
month_value = f"{args.month}-01" if args.month else None

DATABASE_URL = os.environ.get("DATABASE_URL", "")

OUTPUT_FILE = (
    f"rogers_price_validation_{args.month}.xlsx"
    if args.month
    else "rogers_price_validation.xlsx"
)

FUNCTION_SQL_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "rogers_wireless_price_validation_function.sql",
)


# ==============================
# LOAD DATA
# ==============================
print("Connecting to database...")

if not DATABASE_URL:
    raise SystemExit("DATABASE_URL is not set.")

engine = create_engine(DATABASE_URL)

print("Ensuring reporting functions are up to date...")
with open(FUNCTION_SQL_FILE) as f:
    function_sql = f.read()

# Use the raw DBAPI cursor (not conn.exec_driver_sql) so psycopg2 doesn't try
# to treat literal "%" characters in the script (e.g. LIKE '%no charge%') as
# parameter placeholders.
raw_conn = engine.raw_connection()
try:
    with raw_conn.cursor() as cur:
        cur.execute(function_sql)
    raw_conn.commit()
finally:
    raw_conn.close()

with engine.connect() as conn:
    df = pd.read_sql(
        text("SELECT * FROM reporting.validate_rogers_cellular_prices(:month)"),
        conn,
        params={"month": month_value},
    )
    summary = pd.read_sql(
        text("SELECT * FROM reporting.validate_rogers_cellular_summary(:month)"),
        conn,
        params={"month": month_value},
    )

print(f"Total rows loaded: {len(df)}")

# ==============================
# VALIDATION SUMMARY
# ==============================
print("\nValidation Summary")
print("=" * 60)

for _, row in summary.iterrows():
    print(f"{row['metric']}: {row['value']}")

# ==============================
# Match column names/order to rogers_wireless_price_validation.py,
# so this is the same "comparison" shape write_price_validation_workbook()
# already expects from that script.
# ==============================
comparison = df.rename(columns={
    "invoice_date": "Invoice Date",
    "price_book_service_id": "Price Book Service ID",
    "monthly_report_service_id": "Monthly Report Service ID",
    "match_status_service_id": "Match Status (Service ID)",
    "monthly_fixed_fee_from_price_book": "Monthly Fixed Fee (from the Price Book)",
    "billed_amount_rate": "Billed Amount (Rate)",
    "msf_other_options": "MSF_OTHER_OPTIONS",
    "hardware": "HARDWARE",
    "others": "OTHERS",
    "difference_billed_amount_minus_monthly_fixed_fee": "Difference (Billed Amount - Monthly Fixed Fee)",
})[[
    "Invoice Date",
    "Price Book Service ID",
    "Monthly Report Service ID",
    "Match Status (Service ID)",
    "Monthly Fixed Fee (from the Price Book)",
    "Billed Amount (Rate)",
    "MSF_OTHER_OPTIONS",
    "HARDWARE",
    "OTHERS",
    "Difference (Billed Amount - Monthly Fixed Fee)",
]]

# ==============================
# SAVE REPORT
# ==============================
summary_rows = list(summary[["metric", "value"]].itertuples(index=False, name=None))
write_price_validation_workbook(comparison, summary_rows, OUTPUT_FILE)

print("\nValidation completed successfully.")
print(f"Output file: {OUTPUT_FILE}")
