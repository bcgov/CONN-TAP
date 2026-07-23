#!/usr/bin/env python3
"""Build a TELUS "unmatched services" workbook.

Collects every ``raw_data.raw_telus_spend`` row that does **not** match any
service in the TELUS pricebook tables and writes them to an Excel workbook with
one tab per ``YYYY-MM`` (month/year) combination.

Matching (a row is considered MATCHED when any of the following succeed):
  * NG code → pricebook ``service_id``
      - Data:  ``^(NG[0-9]{5})``               → data pricebook
      - Cross: ``^(NG[A-Z0-9]{2,6})``          → data or voice pricebook
  * Exact normalized text: ``detail_description`` equals a pricebook
    ``service_name`` or ``short_service_description`` (data or voice).
  * Cellular plan-name mapping (GoBC / TSMA style) → cellular pricebook
    ``service_id`` (cellular services / catalog / control center / MMS).

The standard spend filter is applied first (excludes balance-forward, taxes,
payments / amount-due, usage, and hardware detail lines) so only real service
rows that failed to match are reported.

Usage
-----
  # All month/year combinations present in the data (one tab each):
  python3 scripts/build_telus_unmatched.py

  # A single month/year (one tab):
  python3 scripts/build_telus_unmatched.py 2025-06

  # Alternate database:
  python3 scripts/build_telus_unmatched.py --dsn postgresql://user:pw@host/db

Requires ``DATABASE_URL`` (or ``--dsn``), ``psycopg`` and ``xlsxwriter``.
Output: scripts/telus_unmatched_spend.xlsx (override with --output).
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import OrderedDict
from datetime import date

import xlsxwriter

try:
    import psycopg
except ImportError:  # pragma: no cover - surfaced at runtime
    psycopg = None

from sheet_utils import NUM_FMT, FONT_NAME

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "telus_unmatched_spend.xlsx")

# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------
# Normalized-name expression reused for spend detail and pricebook columns.
_NORM_DETAIL = (
    "TRIM(REGEXP_REPLACE("
    "REGEXP_REPLACE(LOWER(r.detail_description), '\\*', '', 'g'),"
    " '[^a-z0-9 ]', '', 'g'))"
)


def _norm_pb(col: str) -> str:
    return f"TRIM(REGEXP_REPLACE(LOWER({col}), '[^a-z0-9 ]', '', 'g'))"


_MONTH_FILTER_TOKEN = "-- __MONTH_FILTER__"
_EXTRA_CAT_FILTER_TOKEN = "-- __EXTRA_CAT_FILTER__"


# GoBC / TSMA cellular plan-name → cellular pricebook service_id mapping.
# Mirrors scripts/validation/telus/classification_exploration/07_*.sql.
_CELL_MAP = """
    CASE
      WHEN r.detail_description ~* 'GoBC V&D ULNA [0-9]+GB' THEN
        'XPULNA'
        || REGEXP_REPLACE(r.detail_description, '.*V&D ULNA ([0-9]+)GB.*', '\\1', 'i')
        || CASE
          WHEN REGEXP_REPLACE(r.detail_description, '.*V&D ULNA ([0-9]+)GB.*', '\\1', 'i')
            IN ('1','2','3','4','5','6','7','8','9') THEN 'GB'
          ELSE 'G'
        END
      WHEN r.detail_description ILIKE 'GoBC Data 5GB%'  THEN 'XPTMHS5GB'
      WHEN r.detail_description ILIKE 'GoBC Data 10GB%' THEN 'XPTMHS10G'
      WHEN r.detail_description ILIKE 'GoBC Voice ULNA%' THEN 'XPULNAV01'
      WHEN r.detail_description ILIKE '%High Capacity Data 500GB%' THEN 'XPDAT500G'
      WHEN r.detail_description ILIKE '%High Capacity Data 100GB%' THEN 'XPDAT100G'
      WHEN r.detail_description ILIKE '%High Capacity Data Access%'
        OR r.detail_description ILIKE 'TSMA Data Access%' THEN 'XPHCDATAC'
      WHEN r.detail_description ILIKE '%Public Static IP%' THEN 'XSNGTASIP'
      WHEN r.detail_description ILIKE '%Visual Voicemail%' THEN 'XSNGTAVVM'
      WHEN r.detail_description ILIKE '%Network Priority%' THEN 'XSNGTAPRI'
      WHEN r.detail_description ILIKE '%Vacation Disconnect%' THEN 'XPVAD5'
    END
"""

_BASE_SQL = f"""
WITH data_ids AS (
  SELECT DISTINCT UPPER(TRIM(service_id)) AS sid
  FROM raw_data.raw_telus_data_services_pricebook
  WHERE NULLIF(TRIM(service_id), '') IS NOT NULL
),
voice_ids AS (
  SELECT DISTINCT UPPER(TRIM(service_id)) AS sid
  FROM raw_data.raw_telus_voice_services_pricebook
  WHERE NULLIF(TRIM(service_id), '') IS NOT NULL
),
data_names AS (
  SELECT nm FROM (
    SELECT {_norm_pb('service_name')} AS nm FROM raw_data.raw_telus_data_services_pricebook
    UNION
    SELECT {_norm_pb('short_service_description')} FROM raw_data.raw_telus_data_services_pricebook
  ) n WHERE nm IS NOT NULL AND nm <> ''
),
voice_names AS (
  SELECT nm FROM (
    SELECT {_norm_pb('service_name')} AS nm FROM raw_data.raw_telus_voice_services_pricebook
    UNION
    SELECT {_norm_pb('short_service_description')} FROM raw_data.raw_telus_voice_services_pricebook
  ) n WHERE nm IS NOT NULL AND nm <> ''
),
cell_ids AS (
  SELECT sid FROM (
    SELECT TRIM(service_id) AS sid FROM raw_data.raw_telus_cellular_services_pricebook
    UNION
    SELECT TRIM(service_id) FROM raw_data.raw_telus_cellular_catalog_and_price_list_pricebook
    UNION
    SELECT TRIM(service_id) FROM raw_data.raw_telus_control_center_services_pricebook
    UNION
    SELECT TRIM(service_id) FROM raw_data.raw_telus_cellular_mms_pricebook
  ) c WHERE sid IS NOT NULL AND sid <> ''
),
spend AS (
  SELECT
    r.raw_id,
    date_trunc('month', r.statement_date)::date AS month_start,
    r.statement_date,
    r.sheet_name,
    r.account_number,
    r.service_number,
    r.source,
    r.source_id,
    r.statement_category,
    TRIM(r.detail_description) AS detail_d,
    r.amount,
    UPPER(SUBSTRING(TRIM(r.detail_description) FROM '^(NG[0-9]{{5}})')) AS ng_data,
    UPPER(SUBSTRING(TRIM(r.detail_description) FROM '^(NG[A-Z0-9]{{2,6}})')) AS ng_any,
    {_NORM_DETAIL} AS norm_detail,
    {_CELL_MAP} AS mapped_cell_id
  FROM raw_data.raw_telus_spend AS r
  WHERE COALESCE(LOWER(TRIM(r.statement_section)), '') <> 'balance forward'
    AND LOWER(TRIM(COALESCE(r.detail_description, ''))) NOT IN (
      'hardware purchase charge', 'device discount repayment',
      'monthly telus easy payment', 'device discount repay. canc.',
      'device discount repay. - cr', 'monthly easy payment',
      'telus easy payment balance', 'equipment adjustment'
    )
    AND COALESCE(LOWER(TRIM(r.statement_category)), '') NOT IN (
      'taxes', 'payment', 'payments', 'amount due from last bill', 'usage'
    )
    {_EXTRA_CAT_FILTER_TOKEN}
)
SELECT
  s.month_start,
  s.statement_date,
  s.sheet_name,
  s.account_number,
  s.service_number,
  s.source,
  s.source_id,
  s.statement_category,
  s.detail_d,
  COALESCE(s.ng_data, s.ng_any) AS ng_code,
  s.amount
FROM spend s
WHERE NOT (
       EXISTS (SELECT 1 FROM data_ids  di WHERE di.sid = s.ng_data)
    OR EXISTS (SELECT 1 FROM data_ids  di WHERE di.sid = s.ng_any)
    OR EXISTS (SELECT 1 FROM voice_ids vi WHERE vi.sid = s.ng_any)
    OR EXISTS (SELECT 1 FROM data_names  dn WHERE dn.nm  = s.norm_detail)
    OR EXISTS (SELECT 1 FROM voice_names vn WHERE vn.nm  = s.norm_detail)
    OR EXISTS (SELECT 1 FROM cell_ids  ci WHERE ci.sid = s.mapped_cell_id)
  )
  {_MONTH_FILTER_TOKEN}
ORDER BY s.month_start NULLS FIRST, s.sheet_name, s.amount DESC
"""

# Output columns (header label, source-row index, is_currency).
COLUMNS = [
    ("Statement Date", 1, False),
    ("Entity",         2, False),
    ("Account Number", 3, False),
    ("Service Number", 4, False),
    ("Source",         5, False),
    ("Source ID",      6, False),
    ("Statement Category", 7, False),
    ("Detail Description", 8, False),
    ("NG Code",        9, False),
    ("Amount",         10, True),
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def fetch_unmatched(dsn: str, period: date | None,
                    exclude_categories: "list[str] | None" = None):
    """Return list of row tuples for unmatched spend, optionally for one month.

    exclude_categories: additional ``statement_category`` values to drop
    (case-insensitive) on top of the standard spend filter.
    """
    if psycopg is None:
        raise RuntimeError("psycopg is not installed; run `pip install psycopg`.")

    if period is None:
        month_filter = ""
    else:
        # period is a datetime.date we construct ourselves, so inlining it as a
        # SQL date literal is injection-safe and avoids psycopg treating the
        # many literal '%' characters in the query as parameter placeholders.
        month_filter = f"AND s.month_start = DATE '{period.isoformat()}'"

    if exclude_categories:
        quoted = ", ".join(
            "'" + cat.strip().lower().replace("'", "''") + "'"
            for cat in exclude_categories
        )
        cat_filter = (
            f"AND COALESCE(LOWER(TRIM(r.statement_category)), '') NOT IN ({quoted})"
        )
    else:
        cat_filter = ""

    sql = _BASE_SQL.replace(_MONTH_FILTER_TOKEN, month_filter)
    sql = sql.replace(_EXTRA_CAT_FILTER_TOKEN, cat_filter)
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()


def group_by_month(rows) -> "OrderedDict[str, list]":
    """Group fetched rows into an ordered {tab_name: [rows]} mapping."""
    groups: "OrderedDict[str, list]" = OrderedDict()
    for row in rows:
        month_start = row[0]
        tab = month_start.strftime("%Y-%m") if month_start else "no-date"
        groups.setdefault(tab, []).append(row)
    return groups


# ---------------------------------------------------------------------------
# Workbook writing
# ---------------------------------------------------------------------------
def _sheet_name(tab: str) -> str:
    # Excel sheet names are capped at 31 characters and must be unique.
    return tab[:31]


# Excel allows 1,048,576 rows per worksheet. Leave headroom for the header and
# total rows and split a month across continuation tabs when it overflows.
MAX_DATA_ROWS_PER_SHEET = 1_000_000


def _chunk_tabs(groups: "OrderedDict[str, list]") -> "list[tuple[str, list]]":
    """Expand month groups into (sheet_name, rows) pairs, splitting overflow."""
    out: "list[tuple[str, list]]" = []
    for tab, rows in groups.items():
        if len(rows) <= MAX_DATA_ROWS_PER_SHEET:
            out.append((tab, rows))
            continue
        parts = range(0, len(rows), MAX_DATA_ROWS_PER_SHEET)
        for i, start in enumerate(parts, start=1):
            suffix = "" if i == 1 else f" ({i})"
            out.append((f"{tab}{suffix}", rows[start:start + MAX_DATA_ROWS_PER_SHEET]))
    return out


def write_workbook(groups: "OrderedDict[str, list]", output_path: str,
                   single_period: date | None) -> None:
    wb = xlsxwriter.Workbook(output_path, {"constant_memory": True})

    header_fmt = wb.add_format({
        "bold": True, "font_name": FONT_NAME, "bg_color": "#D9AAD4",
        "border": 1, "align": "center", "valign": "vcenter",
    })
    text_fmt = wb.add_format({"font_name": FONT_NAME, "border": 1})
    date_fmt = wb.add_format({"font_name": FONT_NAME, "border": 1,
                              "num_format": "yyyy-mm-dd"})
    money_fmt = wb.add_format({"font_name": FONT_NAME, "border": 1,
                               "num_format": NUM_FMT})
    total_fmt = wb.add_format({"bold": True, "font_name": FONT_NAME, "border": 1})
    total_money_fmt = wb.add_format({"bold": True, "font_name": FONT_NAME,
                                     "border": 1, "num_format": NUM_FMT})

    # Ensure at least one tab exists even when a single period has no rows.
    if not groups:
        if single_period is not None:
            groups = OrderedDict({single_period.strftime("%Y-%m"): []})
        else:
            groups = OrderedDict({"No unmatched rows": []})

    for tab, rows in _chunk_tabs(groups):
        ws = wb.add_worksheet(_sheet_name(tab))
        # constant_memory mode flushes each row on write, so column widths,
        # freeze panes, and the header must be set before the data rows.
        _apply_widths(ws)
        ws.freeze_panes(1, 0)

        for col_idx, (label, _src, _is_money) in enumerate(COLUMNS):
            ws.write(0, col_idx, label, header_fmt)

        for out_row, row in enumerate(rows, start=1):
            for col_idx, (_label, src_idx, is_money) in enumerate(COLUMNS):
                value = row[src_idx]
                if col_idx == 0:  # statement date
                    if value is not None:
                        ws.write_datetime(out_row, col_idx, value, date_fmt)
                    else:
                        ws.write_blank(out_row, col_idx, None, text_fmt)
                elif is_money:
                    ws.write_number(out_row, col_idx, float(value or 0), money_fmt)
                else:
                    ws.write(out_row, col_idx, "" if value is None else str(value), text_fmt)

        # Total row for the Amount column (written after the data rows, so it
        # remains compatible with constant_memory's top-to-bottom ordering).
        if rows:
            total_row = len(rows) + 1
            label_col = len(COLUMNS) - 2
            ws.write(total_row, label_col, "Total", total_fmt)
            amount_col = len(COLUMNS) - 1
            first = f"{_col_letter(amount_col)}2"
            last = f"{_col_letter(amount_col)}{total_row}"
            ws.write_formula(total_row, amount_col, f"=SUM({first}:{last})", total_money_fmt)

    wb.close()


def _col_letter(idx0: int) -> str:
    col = idx0 + 1
    out = ""
    while col:
        col, rem = divmod(col - 1, 26)
        out = chr(65 + rem) + out
    return out


def _apply_widths(ws) -> None:
    widths = [13, 18, 15, 15, 12, 10, 22, 46, 12, 14]
    for idx, w in enumerate(widths):
        ws.set_column(idx, idx, w)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_period(value: str) -> date:
    try:
        year_s, month_s = value.split("-")
        return date(int(year_s), int(month_s), 1)
    except (ValueError, AttributeError):
        raise argparse.ArgumentTypeError(
            f"Invalid month/year '{value}'. Expected YYYY-MM (e.g. 2025-06)."
        )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a TELUS unmatched-services workbook (one tab per month/year)."
    )
    parser.add_argument(
        "period", nargs="?", type=parse_period, default=None,
        help="Optional month/year as YYYY-MM. Omit to build all months in the data.",
    )
    parser.add_argument(
        "--dsn", default=os.environ.get("DATABASE_URL"),
        help="Postgres DSN. Defaults to the DATABASE_URL environment variable.",
    )
    parser.add_argument(
        "--output", default=OUTPUT_PATH,
        help=f"Output .xlsx path (default: {OUTPUT_PATH}).",
    )
    parser.add_argument(
        "--exclude-recurring", action="store_true",
        help="Exclude rows with statement_category 'Recurring Service Charges'.",
    )
    parser.add_argument(
        "--exclude-other-charges", action="store_true",
        help="Exclude rows with statement_category 'Other Charges and Credits'.",
    )
    args = parser.parse_args(argv)

    if not args.dsn:
        parser.error("No database DSN provided. Set DATABASE_URL or pass --dsn.")

    exclude_categories = []
    if args.exclude_recurring:
        exclude_categories.append("Recurring Service Charges")
    if args.exclude_other_charges:
        exclude_categories.append("Other Charges and Credits")

    rows = fetch_unmatched(args.dsn, args.period, exclude_categories)
    groups = group_by_month(rows)
    write_workbook(groups, args.output, args.period)

    total = sum(len(v) for v in groups.values())
    tabs = len(groups) if groups else 0
    scope = args.period.strftime("%Y-%m") if args.period else "all months"
    print(f"✓ {total} unmatched row(s) across {tabs} tab(s) ({scope}) → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
