#!/usr/bin/env python3
"""Rebuild a monthly NGTA spend report (Rogers or TELUS) from the raw data, with a CATEGORY column added.

For one month and one feed, writes every raw row of that month in the order it was
ingested, with the vendor report's tabs and columns, plus CATEGORY: the category the row
is counted under in the spend report (cellular, data, voice, ...), or 'dropped' when the
report leaves it out (for example a $0 amount, a TELUS exclusion rule, or a BGE the
report doesn't show).
A Rogers cellular row with device hardware shows both parts: 'cellular + cellular_hardware'.
'unknown' is a row counted in the report's Unknown / Other row.
DROPPED_REASON says why a dropped row was left out: '$0 amount', 'BGE not mapped', or for
TELUS the exclusion rule and the seed's reason (e.g. 'excluded detail: provincial sales tax').

Feeds:
  cellular   Rogers cellular (Usage_&_Spend)          month of INVOICE_DATE
  wireline   Rogers wireline (BC_GOV_WIRELINE_RPT)    month of BILLINGDATE
  telus      TELUS consolidated spend, one tab per BGE month of Statement Date
(The spend report puts Rogers cellular spend in the month before the invoice.)

Columns follow each vendor's current layout. Older Rogers reports used other names for
some columns (COMPANY_NAME, CHARGES_SUBTOTAL, ...); the ingestion stored them under the
current ones. File columns the raw table has no column for were kept in `extras` and are
written after the report's columns.

Categories come from intermediate.rpt_spend_lines, the table the spend report reads, so
refresh it first (dbt run --select tag:report).

Run:    python3 scripts/build_ngta_categorised.py 2025-08 cellular
        python3 scripts/build_ngta_categorised.py 2026-03 wireline
        python3 scripts/build_ngta_categorised.py 2026-08 telus
Output: scripts/<feed>_<month>_categorised.xlsx
"""

import os
import sys
from datetime import datetime
from decimal import Decimal
from itertools import groupby
from pathlib import Path

import openpyxl
import psycopg
from openpyxl.utils import get_column_letter

from report_source import DEFAULT_DSN

OUTPUT_DIR = Path(__file__).parent

# Per feed: vendor, raw table, the report date column, which tab a row goes on (SQL), the
# output file name, the report's header for each raw column whose header doesn't follow
# the vendor's usual rule (Rogers: column name in capitals, TELUS: Title Case), and the
# feed's own reasons a row is dropped (SQL, with any joins they need).
# In the SQL, a literal % is written %% (psycopg uses % for parameters).
FEEDS = {
    "cellular": {
        "vendor": "rogers",
        "table": "raw_rogers_spend_cellular",
        "date_column": "invoice_date",
        "tab": "'Usage_&_Spend'",
        "output": "rogers_cellular",
        "headers": {
            "billed_amount_pre_tax": "BILLED_AMOUNT(PRE-TAX)",
            "billed_amount_post_tax": "BILLED_AMOUNT(POST-TAX)",
            "sub_bge": "SUB-BGE",
        },
        # plan part = billed - hardware, hardware part = hardware; both $0 only when both are 0
        "dropped_rules": """
            WHEN coalesce(f.billed_amount_pre_tax, 0) = 0 AND coalesce(f.hardware, 0) = 0 THEN '$0 amount'
        """,
        "dropped_joins": "",
    },
    "wireline": {
        "vendor": "rogers",
        "table": "raw_rogers_spend_data_voice",
        "date_column": "billingdate",
        "tab": "'BC_GOV_WIRELINE_RPT'",
        "output": "rogers_wireline",
        "headers": {
            "billed_amount_pre_tax": "BILLED_AMOUNT(PRE-TAX)",
        },
        "dropped_rules": """
            WHEN coalesce(f.billed_amount_pre_tax, 0) = 0 THEN '$0 amount'
        """,
        "dropped_joins": "",
    },
    "telus": {
        "vendor": "telus",
        "table": "raw_telus_spend",
        "date_column": "statement_date",
        # one tab per BGE, named as in the TELUS file (BCH, GBC, ...)
        "tab": "r.sheet_name",
        "output": "telus",
        "headers": {
            "source_id": "Source ID",
        },
        # The exclusion rules in int_telus_ngta_spend, in its order, with each seed's own reason.
        # Text is cleaned the way dbt cleans it: clean_text + lower for section and category,
        # text_key for the detail description.
        "dropped_rules": """
            WHEN f.statement_date IS NULL THEN 'no statement date'
            WHEN excluded_section.exclusion_reason IS NOT NULL
                THEN 'excluded section: ' || excluded_section.exclusion_reason
            WHEN excluded_detail.exclusion_reason IS NOT NULL
                THEN 'excluded detail: ' || excluded_detail.exclusion_reason
            WHEN excluded_category.exclusion_reason IS NOT NULL
                THEN 'excluded category: ' || excluded_category.exclusion_reason
            WHEN coalesce(f.amount, 0) = 0 THEN '$0 amount'
        """,
        "dropped_joins": r"""
            LEFT JOIN seeds.telus_excluded_sections excluded_section
                ON excluded_section.statement_section
                    = lower(nullif(trim(regexp_replace(f.statement_section, '[\x00-\x20\x7f]+', ' ', 'g')), ''))
            LEFT JOIN seeds.telus_excluded_details excluded_detail
                ON trim(regexp_replace(lower(excluded_detail.detail_description), '[^a-z0-9%%]+', ' ', 'g'))
                    = trim(regexp_replace(lower(f.detail_description), '[^a-z0-9%%]+', ' ', 'g'))
            LEFT JOIN seeds.telus_excluded_categories excluded_category
                ON excluded_category.statement_category
                    = lower(nullif(trim(regexp_replace(f.statement_category, '[\x00-\x20\x7f]+', ' ', 'g')), ''))
        """,
    },
}

# One row per raw row of the month, with its tab, category and dropped reason, tabs in file order.
# A raw row is counted when it has a line in rpt_spend_lines with a BGE.
QUERY = """
    WITH file_rows AS (
        SELECT {tab} AS tab, r.*
        FROM raw_data.{table} r
        JOIN raw_data.ingestion_run run
            ON run.ingestion_run_id = r.ingestion_run_id
        WHERE run.provider = '{vendor}'
            AND date_trunc('month', coalesce(r.{date_column}, run.source_period))::date = %s
    ),

    -- Each row's lines in the spend report; category is only set when a line has a BGE.
    -- A Rogers cellular row with hardware has two lines: 'cellular + cellular_hardware'.
    report_lines AS (
        SELECT
            s.raw_id,
            string_agg(DISTINCT coalesce(s.category, 'unknown'), ' + '
                       ORDER BY coalesce(s.category, 'unknown'))
                FILTER (WHERE s.entity_key IS NOT NULL) AS category
        FROM intermediate.rpt_spend_lines s
        JOIN file_rows f ON f.raw_id = s.raw_id
        WHERE s.source_table = '{table}'
        GROUP BY s.raw_id
    )

    SELECT
        f.*,
        coalesce(l.category, 'dropped') AS category,
        CASE
            WHEN l.category IS NOT NULL THEN NULL
            WHEN l.raw_id IS NOT NULL THEN 'BGE not mapped'
            {dropped_rules}
            -- should not happen; a dropped row none of the rules above explains
            ELSE 'unknown'
        END AS dropped_reason
    FROM file_rows f
    LEFT JOIN report_lines l ON l.raw_id = f.raw_id
    {dropped_joins}
    ORDER BY min(f.raw_id) OVER (PARTITION BY f.tab), f.raw_id
"""

# Our own columns, not part of the vendor report
SKIP_COLUMNS = {"tab", "raw_id", "ingestion_run_id", "sheet_name", "extras", "category", "dropped_reason"}


def header_name(feed: dict, column: str) -> str:
    if column in feed["headers"]:
        return feed["headers"][column]
    if feed["vendor"] == "telus":
        return column.replace("_", " ").title()  # account_number -> Account Number
    return column.upper()


def excel_value(value):
    # Excel has no decimal type
    if isinstance(value, Decimal):
        return float(value)
    return value


def write_tab(wb, tab: str, rows: list[dict], report_columns: list[str], feed: dict) -> None:
    # File columns kept in extras, in the order they first appear
    extra_columns = []
    for row in rows:
        for key in row["extras"] or {}:
            if key not in extra_columns:
                extra_columns.append(key)

    headers = [header_name(feed, c) for c in report_columns] + extra_columns + ["CATEGORY", "DROPPED_REASON"]

    output_rows = []
    for row in rows:
        extras = row["extras"] or {}
        output_rows.append(
            [excel_value(row[c]) for c in report_columns]
            + [extras.get(key) for key in extra_columns]
            + [row["category"], row["dropped_reason"]]
        )

    ws = wb.create_sheet(tab)

    # Column widths and the frozen header row have to be set before any row is written.
    # Each column is as wide as its longest value or header.
    for i, header in enumerate(headers):
        longest = max([len(header)] + [len(str(r[i])) for r in output_rows if r[i] is not None])
        ws.column_dimensions[get_column_letter(i + 1)].width = longest + 4
    ws.freeze_panes = "A2"

    ws.append(headers)
    for output_row in output_rows:
        ws.append(output_row)

    print(f"  {tab}: {len(rows)} rows")


def build(month: str, feed_name: str) -> None:
    feed = FEEDS[feed_name]
    month_start = datetime.strptime(month, "%Y-%m")
    query = QUERY.format(
        tab=feed["tab"],
        table=feed["table"],
        vendor=feed["vendor"],
        date_column=feed["date_column"],
        dropped_rules=feed["dropped_rules"],
        dropped_joins=feed["dropped_joins"],
    )

    wb = openpyxl.Workbook(write_only=True)
    total = 0

    with psycopg.connect(os.environ.get("DATABASE_URL", DEFAULT_DSN)) as conn:
        # A named cursor streams the rows instead of loading the whole month at once;
        # only one tab is held in memory at a time.
        with conn.cursor(name="report_rows") as cur:
            cur.execute(query, (month_start.date(),))
            columns = [col.name for col in cur.description]
            report_columns = [c for c in columns if c not in SKIP_COLUMNS]
            rows = (dict(zip(columns, values)) for values in cur)

            for tab, tab_rows in groupby(rows, key=lambda row: row["tab"]):
                tab_rows = list(tab_rows)
                write_tab(wb, tab, tab_rows, report_columns, feed)
                total += len(tab_rows)

    if total == 0:
        sys.exit(f"No {feed_name} rows for {month}")

    output_path = OUTPUT_DIR / f"{feed['output']}_{month}_categorised.xlsx"
    wb.save(output_path)
    print(f"✓ {total} rows written → {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in FEEDS:
        sys.exit("Usage: python3 scripts/build_ngta_categorised.py <YYYY-MM> <cellular|wireline|telus>")
    build(sys.argv[1], sys.argv[2])
