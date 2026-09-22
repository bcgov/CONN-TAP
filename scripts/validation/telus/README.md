# 📊 Telus Spend Validation (SQL + Python)

## Overview

This project validates the Telus raw spend data in `raw_data.raw_telus_spend` and
generates an Excel report with a detailed issue breakdown per check and a summary sheet.

Unlike the Rogers validators (which run in Python/Pandas over an Excel file), the Telus
validation logic lives in **PostgreSQL functions** defined in the sibling `.sql` files.
A thin Python wrapper (`run_validations.py`) (re)creates those functions, runs each one,
and writes every result to its own worksheet tab.

The project is designed to be:
- Easy to maintain (validation rules stay in versioned SQL)
- Team-friendly
- GitHub-ready
- Aligned with the database as the source of truth

---

## Project Structure

```text
scripts/validation/telus/
│
├── run_validations.py          # Entry point (applies SQL, runs all checks, writes Excel)
├── telus_validation.sql        # Core validation functions
├── spend_comparison.sql        # Month-over-month spend comparison function
├── README.md
│
└── helpers/
    ├── get_duplicates.sql                  # Drill-down: rows behind duplicate check
    ├── get_month_non_date_telus.sql        # Ad-hoc: non-date `month` values
    └── telus_tax_names_with_appearance.sql # Ad-hoc: tax-like descriptions outside Taxes
```

Output is written to the `scripts/` folder as
`telus_validation_report_YYYY-MM.xlsx` (or `telus_validation_report.xlsx` when no month
is given).

---

## Validation Checks

Each check returns the rows where validation **fails**. The month-agnostic checks take an
optional statement month; the month-required checks are skipped when `--month` is omitted.

### 1. Tax-like Detail
Rows outside the `Taxes` category whose `detail_description` looks tax-like
(gst/pst/hst/qst) but is not on the known allowlist.

### 2. Device-like Detail
`Wireless`/blank-source rows whose `detail_description` looks device/hardware/equipment/
Easy-Payment related but is not on the known hardware allowlist.

### 3. Source ID vs Source
Enforces the `source_id` ↔ `source` mapping
(`164`/`130` → Wireless; `1001`/`103`/`104`/`102`/`106` → Wireline).

### 4. Blanks by Sheet
Required columns that contain a NULL or whitespace-only value within a (sheet, month).

### 5. Category Allowlist
`statement_category` values outside the set of known Telus categories.

### 6. Column Value Types
Values that are not coercible to their expected type
(numeric `account_number` / `invoice_number` / `source_id`, and a valid `month` format).

### 7. Duplicate Rows  *(hidden)*
This check exists in SQL but is not currently emitted as a worksheet tab
(it is redundant with Duplicate Summary + All Duplicate Rows).
Uncomment it in `run_validations.py` to include it in the workbook.

### 8. Duplicate Summary
The same duplicate detection as above, summarized per sheet/month with an amount sum.

### 8b. All Duplicate Rows  *(requires `--month`)*
Every individual raw row that is part of a duplicate group — the actual rows behind the
Duplicate Rows / Duplicate Summary counts. Built by looping the existing per-sheet
drill-down `telus_raw_get_duplicate_rows(sheet, year, month)` over every sheet that has
duplicates that month.

### 9. Missing BGEs  *(requires `--month`)*
Expected BGEs (from reference data) that have no matching sheet in the target month.

### 10. New / Removed BGEs  *(requires `--month`)*
Sheet names added or removed compared to the prior month.

### 11. Spend Comparison  *(requires `--month`)*
Month-over-month spend by entity across categories, with a >50% difference flag.
This is a comparison report rather than a strict pass/fail check.

### 12. Cost Validation  *(requires `--month` + pricebook tables)*
Matched TELUS spend whose billed `amount` differs from the pricebook `monthly_fee` by
at least one cent. Reuses `fetch_discrepancies()` from
[build_telus_cost_validation.py](../../build_telus_cost_validation.py).

### 13. Unmatched Spend  *(requires `--month` + pricebook tables)*
Real service rows in `raw_telus_spend` that match no TELUS pricebook service (NG-code,
exact-text, or cellular plan-name mapping). Reuses `fetch_unmatched()` from
[build_telus_unmatched.py](../../build_telus_unmatched.py).

---

## Output Report Structure

| Sheet Name          | Description                                            |
|---------------------|--------------------------------------------------------|
| Summary             | High-level results (issue count + PASS/FAIL/SKIPPED)   |
| Tax-like Detail     | Unlisted tax-like detail descriptions                  |
| Device-like Detail  | Unlisted device/hardware detail descriptions           |
| Source ID vs Source | `source_id` does not match expected `source`           |
| Blanks by Sheet     | Blank/whitespace values in required columns            |
| Category Allowlist  | `statement_category` outside the allowlist             |
| Column Value Types  | Values not coercible to the expected type              |
| Duplicate Summary   | Duplicate rows summary (with amount sum)               |
| All Duplicate Rows  | Every individual raw row in a duplicate group          |
| Missing BGEs        | Expected BGEs with no matching sheet this month        |
| New-Removed BGEs    | Sheets added/removed vs the prior month                |
| Spend Comparison    | Month-over-month spend comparison by entity            |
| Cost Validation     | Billed amount vs pricebook monthly_fee (>= 1 cent diff)|
| Unmatched Spend     | Service rows matching no pricebook service             |

---

## ▶ How to Run

### Install dependencies
```
pip install "psycopg[binary]" pandas openpyxl xlsxwriter
```
(`xlsxwriter` is only needed for the Cost Validation / Unmatched Spend tabs, which reuse
the standalone pricebook scripts; those two tabs are skipped gracefully if it's missing.)

### Set the database connection
```
export DATABASE_URL=postgresql://user:pass@localhost:5432/ngta
```

### Run the pipeline
```
# scoped to one statement month (any date within the month)
python scripts/validation/telus/run_validations.py --month 2026-06-15

# whole table (month-required checks are skipped)
python scripts/validation/telus/run_validations.py
```

### Options

| Option        | Description                                                        |
|---------------|--------------------------------------------------------------------|
| `--dsn`       | Postgres DSN (default: `DATABASE_URL` env var)                     |
| `--month`     | Any date within the target statement month (e.g. `2026-06-15`)     |
| `--output`    | Output `.xlsx` path (default: `scripts/telus_validation_report…`)  |
| `--no-apply`  | Do not (re)create the SQL functions before running                 |

---

## Summary Output Example

| Check              | Description                                                     | Issue_Count | Status  |
|--------------------|----------------------------------------------------------------|-------------|---------|
| Duplicate Rows     | Rows identical on every meaningful column within a (sheet, month). | 12       | FAIL    |
| Category Allowlist | statement_category values outside the set of known Telus categories. | 0     | PASS    |
| Spend Comparison   | Month-over-month spend by entity across categories.            | —           | SKIPPED |
