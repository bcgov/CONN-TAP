# main_wireline.py
# Entry point for the DB-sourced Rogers wireline price validation export.
# Runs reporting.validate_rogers_wireline_prices() (defined in
# rogers_wireline_function.sql) and writes the result to Excel.

import argparse
import os
import pandas as pd
from sqlalchemy import create_engine, text

from report_writer import write_wireline_price_validation_workbook

# ==============================
# CONFIG
# ==============================
parser = argparse.ArgumentParser(description="Rogers wireline price validation export")
parser.add_argument(
    "--billing-date",
    help="Billing date to filter to, format YYYY-MM-DD (default: all billing dates in the raw tables)",
)
args = parser.parse_args()
billing_date_value = args.billing_date

DATABASE_URL = os.environ.get("DATABASE_URL", "")

OUTPUT_FILE = (
    f"rogers_wireline_price_validation_{args.billing_date}.xlsx"
    if args.billing_date
    else "rogers_wireline_price_validation.xlsx"
)

FUNCTION_SQL_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "rogers_wireline_function.sql",
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
# to treat literal "%" characters in the script (e.g. LIKE '%' || ... || '%')
# as parameter placeholders.
raw_conn = engine.raw_connection()
try:
    with raw_conn.cursor() as cur:
        cur.execute(function_sql)
    raw_conn.commit()
finally:
    raw_conn.close()

with engine.connect() as conn:
    comparison = pd.read_sql(
        text('SELECT * FROM reporting.validate_rogers_wireline_prices(:billing_date)'),
        conn,
        params={"billing_date": billing_date_value},
    )

print(f"Total rows loaded: {len(comparison)}")

# ==============================
# VALIDATION SUMMARY
# (mirrors sql_helper/rogers_wireline_summary.sql)
# ==============================
status_sort_order = {
    "Matched": 1,
    "Rate Mismatch": 2,
    "Missing from Price Book": 3,
    "Missing Service ID from Report": 4,
    "Missing Report Rate": 5,
}

status_counts = (
    comparison["Match Status (Service ID)"]
    .value_counts()
    .rename_axis("status")
    .reset_index(name="row_count")
)
status_counts["sort_order"] = status_counts["status"].map(status_sort_order).fillna(98)

summary_rows = [
    (row.status, row.row_count)
    for row in status_counts.sort_values("sort_order").itertuples(index=False)
]
summary_rows.append(("Total Rows", len(comparison)))

print("\nValidation Summary")
print("=" * 60)
for label, value in summary_rows:
    print(f"{label}: {value}")

# ==============================
# SAVE REPORT
# ==============================
missing_service_id_report = comparison[
    comparison["Match Status (Service ID)"] == "Missing Service ID from Report"
]

write_wireline_price_validation_workbook(
    comparison,
    summary_rows,
    OUTPUT_FILE,
    missing_service_id_df=missing_service_id_report,
)

print("\nValidation completed successfully.")
print(f"Output file: {OUTPUT_FILE}")
