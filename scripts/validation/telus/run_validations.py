#!/usr/bin/env python3
"""Run every Telus raw-spend validation and export the results to one Excel workbook.

Each validation goes into its own worksheet tab, plus a leading ``Summary`` tab that
lists the row (issue) count and PASS/FAIL status for every check.

Most validation logic lives in the sibling ``.sql`` files as Postgres functions against
``raw_data.raw_telus_spend``. By default this script (re)creates those functions from the
SQL files before running them, so the workbook always reflects the current SQL. The
pricebook checks (Cost Validation, Unmatched Spend) reuse the fetch functions of the
standalone ``scripts/build_telus_cost_validation.py`` and ``scripts/build_telus_unmatched.py``.

Usage
-----
  export DATABASE_URL=postgresql://user:pass@localhost:5432/ngta
  python scripts/validation/telus/run_validations.py --month 2026-06-15

  # or point at a specific DSN / output file, and scan the whole table (no month filter)
  python scripts/validation/telus/run_validations.py --dsn "$DATABASE_URL"

Notes
-----
* ``--month`` accepts any date inside the target statement month (e.g. 2026-06-15).
  When omitted, the month-agnostic validators scan the entire table; the validators
  that require a month (missing/new BGEs, spend comparison, cost validation, unmatched
  spend) are skipped.
* Requires: psycopg (v3), pandas, and openpyxl. The Cost Validation / Unmatched Spend
  tabs additionally need xlsxwriter (imported by the reused pricebook scripts) and the
  loaded pricebook tables; they are skipped gracefully if xlsxwriter is missing.
    pip install "psycopg[binary]" pandas openpyxl xlsxwriter
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path

import pandas as pd

try:
    import psycopg
except ImportError:  # pragma: no cover - dependency hint
    print("psycopg (v3) is required: pip install 'psycopg[binary]'", file=sys.stderr)
    raise

HERE = Path(__file__).resolve().parent
# scripts/validation/telus -> scripts
SCRIPTS_DIR = HERE.parent.parent

# SQL files that contain CREATE [OR REPLACE] FUNCTION definitions to (re)load.
# checks/*.sql are applied in filename order -- 00_bge_alias_matches.sql defines
# telus_bge_alias_matches, which several later checks call, so it must load first.
# checks/13_spend_comparison.sql defines the month-over-month comparison function.
DDL_FILES = [
    *sorted(HERE.glob("checks/*.sql")),
    HERE / "helpers" / "get_duplicates.sql",
]

# How each check runs. A "runner" takes (conn, month, dsn) and returns a DataFrame of
# failing rows, or None when the check is skipped (e.g. it needs a month and none was
# given). The small builders below let the VALIDATIONS table stay declarative and keep
# the run loop to a single call.

def check(sql):
    """SQL check with an optional month filter: scans the whole table, or one month."""
    def run(conn, month, dsn):
        return run_query(conn, sql, (month,))
    return run


def monthly_check(sql):
    """SQL check that only runs when a month is given (skipped otherwise)."""
    def run(conn, month, dsn):
        return None if month is None else run_query(conn, sql, (month,))
    return run


def spend_check(sql):
    """Spend comparison: needs a month, passed to the function as (year, month)."""
    def run(conn, month, dsn):
        return None if month is None else run_query(conn, sql, (month.year, month.month))
    return run


def duplicate_rows_check(conn, month, dsn):
    """Every individual duplicate row, gathered per sheet (needs a month)."""
    return None if month is None else run_all_duplicate_rows(conn, month)


def pricebook_check(module_name, fetch_name):
    """Reuse a scripts/ pricebook validator's fetch function for one month."""
    def run(conn, month, dsn):
        if month is None:
            return None
        try:
            return run_pricebook_validation(module_name, fetch_name, dsn, month)
        except ImportError:
            return None  # xlsxwriter not installed; skip these optional tabs
    return run


# Each validation: (worksheet tab, description, runner).
# Tab names are kept <= 31 chars (Excel limit) and free of []:*?/\ characters.
VALIDATIONS = [
    ("Tax-like Detail",
     "Rows outside the Taxes category whose detail_description looks tax-like "
     "(gst/pst/hst/qst) but is not on the known allowlist.",
     check("SELECT * FROM telus_raw_validate_unlisted_tax_like_detail_descriptions(%s)")),
    ("Device-like Detail",
     "Wireless/blank-source rows whose detail_description looks device/hardware/"
     "equipment/Easy-Payment related but is not on the known hardware allowlist.",
     check("SELECT * FROM telus_raw_validate_unlisted_device_related_detail_descriptions(%s)")),
    ("Source ID vs Source",
     "Enforces the source_id to source mapping "
     "(164/130 -> Wireless; 1001/103/104/102/106 -> Wireline).",
     check("SELECT * FROM telus_raw_validate_source_id_matches_expected_source(%s)")),
    ("Blanks by Sheet",
     "Required columns that contain a NULL or whitespace-only value within a (sheet, month).",
     check("SELECT * FROM telus_raw_validate_blanks_by_sheet_and_month(%s)")),
    ("Category Allowlist",
     "statement_category values outside the set of known Telus categories.",
     check("SELECT * FROM telus_raw_validate_statement_category_allowlist(%s)")),
    ("Column Value Types",
     "Values not coercible to their expected type (numeric account_number/invoice_number/"
     "source_id, and a valid month format).",
     check("SELECT * FROM telus_raw_validate_column_value_types(%s)")),
    # Hidden -- redundant with Duplicate Summary + All Duplicate Rows (same detection). The
    # SQL function still exists; uncomment to restore the per-sheet/month duplicate tab.
    # ("Duplicate Rows",
    #  "Rows that are identical on every meaningful column within a (sheet, month).",
    #  check("SELECT * FROM telus_raw_validate_duplicate_rows_by_sheet_and_month(%s)")),
    ("Duplicate Summary",
     "Duplicate rows summarized per sheet/month with an amount sum.",
     check("SELECT * FROM telus_raw_summarize_duplicate_rows_by_sheet_and_month(%s)")),
    ("All Duplicate Rows",
     "Every individual raw row that is part of a duplicate group (the rows behind the "
     "Duplicate Summary counts). Requires --month.",
     duplicate_rows_check),
    ("Missing BGEs",
     "Expected BGEs (from reference data) that have no matching sheet in the target month.",
     monthly_check("SELECT * FROM telus_raw_validate_all_bges_in_sheets(%s)")),
    ("New-Removed BGEs",
     "Sheet names added or removed compared to the prior month.",
     monthly_check("SELECT * FROM telus_raw_validate_new_bges_in_sheets(%s)")),
    ("New-Removed Sub-BGEs",
     "account_description values (sub-organizations) added or removed compared to the prior month.",
     monthly_check("SELECT * FROM telus_raw_validate_new_sub_bges_in_accounts(%s)")),
    ("Spend Comparison",
     "Month-over-month spend by entity across categories, with a >50% difference flag "
     "(comparison report rather than a strict pass/fail check).",
     spend_check("SELECT * FROM raw_data.fn_telus_spend_comparison(%s, %s)")),
    ("Cost Validation",
     "Matched TELUS spend whose billed amount differs from the pricebook monthly_fee by "
     ">= 1 cent. Requires --month and the loaded pricebook tables.",
     pricebook_check("build_telus_cost_validation", "fetch_discrepancies")),
    ("Unmatched Spend",
     "Real service rows in raw_telus_spend that match no TELUS pricebook service "
     "(NG-code, exact-text, or cellular plan-name). Requires --month and the pricebook tables.",
     pricebook_check("build_telus_unmatched", "fetch_unmatched")),
]


def parse_month(value: str | None) -> dt.date | None:
    """Parse --month (any date within the target month) into a date, or None."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y/%m/%d", "%Y/%m"):
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"--month must be a date like 2026-06-15 or 2026-06 (got {value!r})"
    )


def apply_ddl(conn: "psycopg.Connection") -> None:
    """(Re)create the validation functions from the sibling SQL files."""
    for path in DDL_FILES:
        if not path.exists():
            print(f"  ! missing DDL file, skipping: {path}", file=sys.stderr)
            continue
        conn.execute(path.read_text())
        print(f"  applied {path.relative_to(SCRIPTS_DIR.parent)}")
    conn.commit()


def run_query(conn: "psycopg.Connection", sql: str, params: tuple) -> pd.DataFrame:
    """Execute a validation query and return the result as a DataFrame."""
    with conn.cursor() as cur:
        cur.execute(sql, params)
        columns = [d.name for d in cur.description] if cur.description else []
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=columns)


def run_all_duplicate_rows(conn: "psycopg.Connection", month: dt.date) -> pd.DataFrame:
    """Return every duplicate raw row for the month by looping the per-sheet drill-down.

    Reuses telus_raw_get_duplicate_rows(sheet, year, month): first find the sheets that
    have duplicates that month (via the summary validator), then fetch their rows and stack.
    """
    sheets = run_query(
        conn,
        "SELECT DISTINCT sheet_name "
        "FROM telus_raw_validate_duplicate_rows_by_sheet_and_month(%s)",
        (month,),
    )
    frames = []
    for sheet in sheets["sheet_name"] if not sheets.empty else []:
        df = run_query(
            conn,
            "SELECT * FROM telus_raw_get_duplicate_rows(%s, %s, %s)",
            (sheet, month.year, month.month),
        )
        if not df.empty:
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def run_pricebook_validation(module_name: str, fetch_name: str,
                             dsn: str, month: dt.date) -> pd.DataFrame:
    """Reuse a scripts/ pricebook validator's fetch function for a single month.

    Imports the standalone module (build_telus_cost_validation / build_telus_unmatched),
    calls its fetch function for the report month, and shapes the row tuples into a
    DataFrame using the module's COLUMNS (label, source-index) mapping.
    """
    import importlib

    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    mod = importlib.import_module(module_name)
    fetch = getattr(mod, fetch_name)

    period = dt.date(month.year, month.month, 1)
    rows = fetch(dsn, period, None)

    labels = [col[0] for col in mod.COLUMNS]
    indices = [col[1] for col in mod.COLUMNS]
    data = [[row[i] for i in indices] for row in rows]
    return pd.DataFrame(data, columns=labels)


# Excel allows 1,048,576 rows per sheet (including the header). Keep headroom and split
# any larger result across continuation tabs (" (2)", " (3)", ...), like the standalone
# pricebook scripts do.
MAX_DATA_ROWS_PER_SHEET = 1_000_000


def sheet_chunks(tab: str, frame: pd.DataFrame):
    """Yield (sheet_name, chunk) pairs, splitting frames that exceed Excel's row cap.

    Sheet names are kept within Excel's 31-char limit, leaving room for the suffix.
    """
    if len(frame) <= MAX_DATA_ROWS_PER_SHEET:
        yield tab[:31], frame
        return
    for i, start in enumerate(range(0, len(frame), MAX_DATA_ROWS_PER_SHEET)):
        suffix = "" if i == 0 else f" ({i + 1})"
        yield f"{tab[:31 - len(suffix)]}{suffix}", frame.iloc[start:start + MAX_DATA_ROWS_PER_SHEET]


def _style_report(output: Path) -> None:
    """Apply the shared cosmetic Excel styling (best-effort -- never fails the run)."""
    try:
        validation_dir = next(
            p for p in Path(__file__).resolve().parents if p.name == "validation"
        )
        if str(validation_dir) not in sys.path:
            sys.path.insert(0, str(validation_dir))
        from report_style import style_workbook
        style_workbook(output)
    except Exception as exc:  # styling is cosmetic; a failure must not break the report
        print(f"  (report styling skipped: {exc})", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dsn", default=os.environ.get("DATABASE_URL"),
                        help="Postgres DSN (default: env DATABASE_URL)")
    parser.add_argument("--month", type=str, default=None,
                        help="Any date within the target statement month, e.g. 2026-06-15. "
                             "Omit to scan all months (month-required checks are then skipped).")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output .xlsx path (default: scripts/telus_validation_report[_YYYY-MM].xlsx)")
    parser.add_argument("--no-apply", action="store_true",
                        help="Do not (re)create the SQL functions before running.")
    args = parser.parse_args()

    if not args.dsn:
        print("Set DATABASE_URL or pass --dsn", file=sys.stderr)
        return 2

    month = parse_month(args.month)

    if args.output is not None:
        output = args.output
    else:
        suffix = f"_{month:%Y-%m}" if month else ""
        output = SCRIPTS_DIR / f"telus_validation_report{suffix}.xlsx"

    print("Connecting to database ...")
    with psycopg.connect(args.dsn) as conn:
        # The helper SQL (get_duplicates.sql) references raw_telus_spend unqualified,
        # so raw_data must be on the search_path for both DDL and the validation calls.
        conn.execute("SET search_path TO raw_data, public")
        if not args.no_apply:
            print("Applying validation SQL functions:")
            apply_ddl(conn)

        results: list[tuple[str, str, pd.DataFrame | None]] = []
        for tab, description, runner in VALIDATIONS:
            df = runner(conn, month, args.dsn)
            if df is None:
                print(f"  - {tab}: SKIPPED (needs --month)")
            else:
                print(f"  - {tab}: {len(df)} row(s)")
            results.append((tab, description, df))

    # Summary sheet: one row per check with description, issue count + status.
    summary_rows = []
    for tab, description, df in results:
        if df is None:
            status, count = "SKIPPED", None
        else:
            count = len(df)
            status = "PASS" if count == 0 else "FAIL"
        summary_rows.append({"Check": tab, "Description": description,
                             "Issue_Count": count, "Status": status})
    summary_df = pd.DataFrame(summary_rows,
                              columns=["Check", "Description", "Issue_Count", "Status"])

    output.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output) as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        for tab, _description, df in results:
            frame = df if df is not None else pd.DataFrame({"note": ["SKIPPED (needs --month)"]})
            if len(frame) > MAX_DATA_ROWS_PER_SHEET:
                print(f"  ! {tab}: {len(frame)} rows exceed one sheet; splitting into tabs")
            for sheet_name, chunk in sheet_chunks(tab, frame):
                chunk.to_excel(writer, sheet_name=sheet_name, index=False)

    _style_report(output)
    print(f"\nValidation report saved to: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
