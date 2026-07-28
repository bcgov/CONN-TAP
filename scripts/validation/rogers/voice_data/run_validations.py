#!/usr/bin/env python3
"""Run every Rogers NGTA data/voice validation and export the results to one Excel workbook.

Each validation goes into its own worksheet tab, plus a leading ``Summary`` tab that lists
the row (issue) count and PASS/FAIL status for every check -- reproducing the tabs of the
legacy Python/Excel report, plus a month-over-month New/Removed detection and (with --month)
a Spend Comparison.

Like the cellular validator, the validation logic lives in the sibling
``validation_rogers_ngta_data_voice.sql`` as Postgres functions against
``raw_data.raw_rogers_spend_data_voice`` and the ``seeds``/``reference_data`` tables. By
default this script (re)creates those functions before running them, so the workbook always
reflects the current SQL.

Usage
-----
  export DATABASE_URL=postgresql://app:app@localhost:5432/app
  python scripts/validation/rogers/voice_data/run_validations.py

  # scope to one statement month (any date within it); adds the Spend Comparison tab
  python scripts/validation/rogers/voice_data/run_validations.py --month 2026-06

Notes
-----
* The default DSN targets the local docker Postgres from app/docker-compose.yml
  (postgresql://app:app@localhost:5432/app). Override with DATABASE_URL or --dsn.
* Requires: psycopg (v3), pandas, and openpyxl.
    pip install "psycopg[binary]" pandas openpyxl
* Prerequisite tables must already be loaded: raw_data.raw_rogers_spend_data_voice,
  seeds.bge_alias_map, seeds.sub_bge_alias_map, reference_data.bge, reference_data.sub_bge.
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
# scripts/validation/rogers/voice_data -> scripts
SCRIPTS_DIR = HERE.parents[2]

# SQL files that contain the CREATE [OR REPLACE] VIEW/FUNCTION definitions to (re)load.
# spend_comparison.sql lives at the Rogers level (it spans cellular + voice/data).
DDL_FILES = [
    HERE.parent / "_shared.sql",
    HERE / "validation_rogers_ngta_data_voice.sql",
    HERE.parent / "spend_comparison.sql",
]

# Default local docker DSN (app/docker-compose.yml: user/pass/db all "app").
DEFAULT_DSN = "postgresql://app:app@localhost:5432/app"

# Each validation: (worksheet tab, description, SQL that returns the failing rows).
# Tab names are kept <= 31 chars (Excel limit) and free of []:*?/\ characters.
VALIDATIONS = [
    ("Duplicate Rows",
     "Every row in a full-row duplicate group.",
     "SELECT * FROM raw_data.rogers_data_voice_duplicates(%s)"),
    ("Null BGE",
     "Rows whose raw BGE is null or blank.",
     "SELECT * FROM raw_data.rogers_data_voice_null_bge(%s)"),
    ("Null SUB-BGE",
     "Rows whose raw SUB-BGE is null or blank.",
     "SELECT * FROM raw_data.rogers_data_voice_null_sub_bge(%s)"),
    ("Missing BGEs",
     "Real BGEs (from reference data) that no report row resolves to.",
     "SELECT * FROM raw_data.rogers_data_voice_missing_bges(%s)"),
    ("Missing SUB-BGEs",
     "Real SUB-BGEs (from reference data) that no report row resolves to, with related BGE.",
     "SELECT * FROM raw_data.rogers_data_voice_missing_sub_bges(%s)"),
    ("Mapping Issues",
     "Rows where the reported BGE differs from the BGE expected by its SUB-BGE.",
     "SELECT * FROM raw_data.rogers_data_voice_mapping_issues(%s)"),
    ("Mapping Summary",
     "The mapping issues rolled up by SUB-BGE / reported BGE / expected BGE, with counts.",
     "SELECT * FROM raw_data.rogers_data_voice_mapping_summary(%s)"),
    ("Unknown SUB-BGEs",
     "SUB-BGE values present in the report that resolve to no BGE.",
     "SELECT * FROM raw_data.rogers_data_voice_unknown_sub_bge(%s)"),
    ("New BGEs",
     "Report BGE values with no alias mapping (unrecognized raw names).",
     "SELECT * FROM raw_data.rogers_data_voice_new_bges(%s)"),
    ("Product Line Issues",
     "Rows whose PRODUCTLINE is outside the allowed set (DATA / VOICE / N/A).",
     "SELECT * FROM raw_data.rogers_data_voice_productline_issues(%s)"),
    ("Pre-Tax Issues",
     "Rows where TOTALAMOUNT minus GST/PST does not reconcile to PRE-TAX (0.01 tolerance).",
     "SELECT * FROM raw_data.rogers_data_voice_pre_tax_issues(%s)"),
    ("Post-Tax Issues",
     "Rows where PRE-TAX plus GST/PST does not reconcile to TOTALAMOUNT (0.01 tolerance).",
     "SELECT * FROM raw_data.rogers_data_voice_post_tax_issues(%s)"),
    # Hidden for now -- the detection function still exists in the SQL; uncomment to show it.
    # ("New-Removed BGEs",
    #  "Month-over-month BGE / SUB-BGE changes: Newly Appeared, Unrecognized, "
    #  "New + Unrecognized, Removed, Still Removed.",
    #  "SELECT * FROM raw_data.rogers_data_voice_new_removed_detection(%s)"),
]


def parse_month(value: str | None) -> "dt.date | None":
    """Parse --month (any date within the target month) into a date, or None for all months."""
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
    """(Re)create the validation view/functions from the sibling SQL files."""
    for path in DDL_FILES:
        if not path.exists():
            print(f"  ! missing DDL file, skipping: {path}", file=sys.stderr)
            continue
        conn.execute(path.read_text())
        print(f"  applied {path.relative_to(SCRIPTS_DIR.parent)}")
    conn.commit()


def run_query(conn: "psycopg.Connection", sql: str, params: tuple = ()) -> pd.DataFrame:
    """Execute a validation query and return the result as a DataFrame."""
    with conn.cursor() as cur:
        cur.execute(sql, params)
        columns = [d.name for d in cur.description] if cur.description else []
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=columns)


def build_summary(results: list[tuple]) -> pd.DataFrame:
    """One row per check: description, row count and PASS/FAIL status."""
    rows = [
        {"Check": tab, "Description": description,
         "Row_Count": len(df), "Status": "PASS" if df.empty else "FAIL"}
        for tab, description, df in results
    ]
    return pd.DataFrame(rows, columns=["Check", "Description", "Row_Count", "Status"])


# Excel allows 1,048,576 rows per sheet (including the header). Keep headroom and split any
# larger result across continuation tabs (" (2)", " (3)", ...).
MAX_DATA_ROWS_PER_SHEET = 1_000_000


def sheet_chunks(tab: str, frame: pd.DataFrame):
    """Yield (sheet_name, chunk) pairs, splitting frames that exceed Excel's row cap."""
    if len(frame) <= MAX_DATA_ROWS_PER_SHEET:
        yield tab[:31], frame
        return
    for i, start in enumerate(range(0, len(frame), MAX_DATA_ROWS_PER_SHEET)):
        suffix = "" if i == 0 else f" ({i + 1})"
        yield f"{tab[:31 - len(suffix)]}{suffix}", frame.iloc[start:start + MAX_DATA_ROWS_PER_SHEET]


def write_workbook(output: Path, results: list[tuple]) -> None:
    """Write the Summary tab plus one tab per check to an .xlsx workbook."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output) as writer:
        build_summary(results).to_excel(writer, sheet_name="Summary", index=False)
        for tab, _description, df in results:
            if len(df) > MAX_DATA_ROWS_PER_SHEET:
                print(f"  ! {tab}: {len(df)} rows exceed one sheet; splitting into tabs")
            for sheet_name, chunk in sheet_chunks(tab, df):
                chunk.to_excel(writer, sheet_name=sheet_name, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dsn", default=os.environ.get("DATABASE_URL", DEFAULT_DSN),
                        help="Postgres DSN (default: env DATABASE_URL, else the local "
                             "docker DSN postgresql://app:app@localhost:5432/app)")
    parser.add_argument("--month", type=str, default=None,
                        help="Any date within the target statement month, e.g. 2026-06-15 "
                             "or 2026-06. Omit to scan all months.")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output .xlsx path (default: "
                             "scripts/rogers_data_voice_validation_report[_YYYY-MM].xlsx)")
    parser.add_argument("--no-apply", action="store_true",
                        help="Do not (re)create the SQL view/functions before running.")
    args = parser.parse_args()

    month = parse_month(args.month)

    if args.output is not None:
        output = args.output
    else:
        suffix = f"_{month:%Y-%m}" if month else ""
        output = SCRIPTS_DIR / f"rogers_data_voice_validation_report{suffix}.xlsx"

    print("Connecting to database ...")
    with psycopg.connect(args.dsn) as conn:
        if not args.no_apply:
            print("Applying validation SQL:")
            apply_ddl(conn)

        results: list[tuple[str, str, pd.DataFrame]] = []
        for tab, description, sql in VALIDATIONS:
            df = run_query(conn, sql, (month,))
            print(f"  - {tab}: {len(df)} row(s)")
            results.append((tab, description, df))

        # Month-over-month spend comparison, scoped to the voice/data feed. Needs a target
        # month and (year, month) args, so it's only included when --month is given.
        if month is not None:
            df = run_query(
                conn,
                "SELECT * FROM raw_data.fn_rogers_spend_comparison(%s, %s, %s)",
                (month.year, month.month, "data_voice"),
            )
            print(f"  - Spend Comparison: {len(df)} row(s)")
            results.append((
                "Spend Comparison",
                "Month-over-month voice/data spend by BGE per category (data/voice/other/"
                "total): current, previous, difference, and a >50% change flag.",
                df,
            ))
        else:
            print("  - Spend Comparison: SKIPPED (needs --month)")

    write_workbook(output, results)
    print(f"\nValidation report saved to: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
