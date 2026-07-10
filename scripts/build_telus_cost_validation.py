#!/usr/bin/env python3
"""Build a TELUS "pricebook cost validation" workbook.

Takes every ``raw_data.raw_telus_spend`` row that **matches** a TELUS pricebook
service, compares the billed ``amount`` against the pricebook ``monthly_fee``,
and reports every row whose billed amount differs from the pricebook cost by at
least one cent (higher or lower). Output is one tab per ``YYYY-MM``.

Matching reuses the logic from build_telus_unmatched.py (NG code → service_id,
exact normalized text on service_name / short_service_description, and cellular
plan-name mapping). For each matched row the authoritative pricebook fee is
chosen by precedence:

  1. Data pricebook via NG code
  2. Voice pricebook via NG code
  3. Data pricebook via exact text
  4. Voice pricebook via exact text
  5. Cellular pricebooks via plan-name mapping

Within the chosen source, when a service maps to several fees (e.g. some voice
service_ids), the fee **closest** to the billed amount is used, so a legitimate
alternate price is not falsely reported.

Only pricebook fees that parse to a clean dollar value are comparable; entries
like ``$5/SIM on all lines`` or blank fees are skipped (not reported).

Usage
-----
  export DATABASE_URL=postgresql://app:app@localhost:5432/app

  # All months:
  python3 scripts/build_telus_cost_validation.py

  # Single month:
  python3 scripts/build_telus_cost_validation.py 2025-06

  # Optional category exclusions (compose freely):
  python3 scripts/build_telus_cost_validation.py 2025-06 --exclude-recurring
  python3 scripts/build_telus_cost_validation.py 2025-06 --exclude-other-charges

Requires ``DATABASE_URL`` (or ``--dsn``), ``psycopg`` and ``xlsxwriter``.
Output: scripts/telus_cost_validation.xlsx (override with --output).
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

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "telus_cost_validation.xlsx")

# Report a discrepancy when |billed amount - pricebook fee| >= this value.
COST_TOLERANCE = 0.01

# ---------------------------------------------------------------------------
# SQL fragments
# ---------------------------------------------------------------------------
_NORM_DETAIL = (
    "TRIM(REGEXP_REPLACE("
    "REGEXP_REPLACE(LOWER(r.detail_description), '\\*', '', 'g'),"
    " '[^a-z0-9 ]', '', 'g'))"
)


def _norm_pb(col: str) -> str:
    return f"TRIM(REGEXP_REPLACE(LOWER({col}), '[^a-z0-9 ]', '', 'g'))"


def _fee_num(col: str) -> str:
    """Parse a pricebook monthly_fee text into numeric, or NULL if not a clean $ value."""
    stripped = f"REGEXP_REPLACE({col}, '[\\s$,]', '', 'g')"
    return (
        f"CASE WHEN {col} IS NOT NULL AND {stripped} ~ '^[0-9]+(\\.[0-9]+)?$' "
        f"THEN {stripped}::numeric END"
    )


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

_MONTH_FILTER_TOKEN = "-- __MONTH_FILTER__"
_EXTRA_CAT_FILTER_TOKEN = "-- __EXTRA_CAT_FILTER__"

_BASE_SQL = f"""
WITH data_id_fee AS (
  SELECT sid, MIN(service_id) AS service_id,
         ARRAY_AGG(fee_num) FILTER (WHERE fee_num IS NOT NULL) AS fees
  FROM (
    SELECT UPPER(TRIM(service_id)) AS sid, TRIM(service_id) AS service_id,
           {_fee_num('monthly_fee')} AS fee_num
    FROM raw_data.raw_telus_data_services_pricebook
    WHERE NULLIF(TRIM(service_id), '') IS NOT NULL
  ) d GROUP BY sid HAVING COUNT(fee_num) > 0
),
voice_id_fee AS (
  SELECT sid, MIN(service_id) AS service_id,
         ARRAY_AGG(fee_num) FILTER (WHERE fee_num IS NOT NULL) AS fees
  FROM (
    SELECT UPPER(TRIM(service_id)) AS sid, TRIM(service_id) AS service_id,
           {_fee_num('monthly_fee')} AS fee_num
    FROM raw_data.raw_telus_voice_services_pricebook
    WHERE NULLIF(TRIM(service_id), '') IS NOT NULL
  ) v GROUP BY sid HAVING COUNT(fee_num) > 0
),
data_name_fee AS (
  SELECT name_norm, MIN(service_id) AS service_id,
         ARRAY_AGG(fee_num) FILTER (WHERE fee_num IS NOT NULL) AS fees
  FROM (
    SELECT {_norm_pb('service_name')} AS name_norm, TRIM(service_id) AS service_id,
           {_fee_num('monthly_fee')} AS fee_num FROM raw_data.raw_telus_data_services_pricebook
    UNION ALL
    SELECT {_norm_pb('short_service_description')}, TRIM(service_id),
           {_fee_num('monthly_fee')} FROM raw_data.raw_telus_data_services_pricebook
  ) x WHERE name_norm IS NOT NULL AND name_norm <> ''
  GROUP BY name_norm HAVING COUNT(fee_num) > 0
),
voice_name_fee AS (
  SELECT name_norm, MIN(service_id) AS service_id,
         ARRAY_AGG(fee_num) FILTER (WHERE fee_num IS NOT NULL) AS fees
  FROM (
    SELECT {_norm_pb('service_name')} AS name_norm, TRIM(service_id) AS service_id,
           {_fee_num('monthly_fee')} AS fee_num FROM raw_data.raw_telus_voice_services_pricebook
    UNION ALL
    SELECT {_norm_pb('short_service_description')}, TRIM(service_id),
           {_fee_num('monthly_fee')} FROM raw_data.raw_telus_voice_services_pricebook
  ) x WHERE name_norm IS NOT NULL AND name_norm <> ''
  GROUP BY name_norm HAVING COUNT(fee_num) > 0
),
cell_id_fee AS (
  SELECT sid, MIN(pb) AS pb, MIN(service_id) AS service_id,
         ARRAY_AGG(fee_num) FILTER (WHERE fee_num IS NOT NULL) AS fees
  FROM (
    SELECT TRIM(service_id) AS sid, TRIM(service_id) AS service_id, 'cellular_services' AS pb,
           {_fee_num('monthly_fee')} AS fee_num FROM raw_data.raw_telus_cellular_services_pricebook
    UNION ALL
    SELECT TRIM(service_id), TRIM(service_id), 'cellular_catalog',
           {_fee_num('monthly_fee')} FROM raw_data.raw_telus_cellular_catalog_and_price_list_pricebook
    UNION ALL
    SELECT TRIM(service_id), TRIM(service_id), 'control_center',
           {_fee_num('monthly_fee')} FROM raw_data.raw_telus_control_center_services_pricebook
    UNION ALL
    SELECT TRIM(service_id), TRIM(service_id), 'cellular_mms',
           {_fee_num('monthly_fee')} FROM raw_data.raw_telus_cellular_mms_pricebook
  ) x WHERE sid IS NOT NULL AND sid <> ''
  GROUP BY sid HAVING COUNT(fee_num) > 0
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
    AND r.amount IS NOT NULL
    {_EXTRA_CAT_FILTER_TOKEN}
),
matched AS (
  SELECT
    s.*,
    -- Chosen match by precedence: data-ng, voice-ng, data-text, voice-text, cellular.
    CASE
      WHEN dng.sid IS NOT NULL OR dng2.sid IS NOT NULL THEN 'data'
      WHEN vng.sid IS NOT NULL THEN 'voice'
      WHEN dnm.name_norm IS NOT NULL THEN 'data'
      WHEN vnm.name_norm IS NOT NULL THEN 'voice'
      WHEN cel.sid IS NOT NULL THEN 'cellular'
    END AS match_type,
    CASE
      WHEN dng.sid IS NOT NULL OR dng2.sid IS NOT NULL THEN 'data_services'
      WHEN vng.sid IS NOT NULL THEN 'voice_services'
      WHEN dnm.name_norm IS NOT NULL THEN 'data_services'
      WHEN vnm.name_norm IS NOT NULL THEN 'voice_services'
      WHEN cel.sid IS NOT NULL THEN cel.pb
    END AS pb,
    CASE
      WHEN dng.sid IS NOT NULL THEN dng.service_id
      WHEN dng2.sid IS NOT NULL THEN dng2.service_id
      WHEN vng.sid IS NOT NULL THEN vng.service_id
      WHEN dnm.name_norm IS NOT NULL THEN dnm.service_id
      WHEN vnm.name_norm IS NOT NULL THEN vnm.service_id
      WHEN cel.sid IS NOT NULL THEN cel.service_id
    END AS ref,
    CASE
      WHEN dng.sid IS NOT NULL THEN dng.fees
      WHEN dng2.sid IS NOT NULL THEN dng2.fees
      WHEN vng.sid IS NOT NULL THEN vng.fees
      WHEN dnm.name_norm IS NOT NULL THEN dnm.fees
      WHEN vnm.name_norm IS NOT NULL THEN vnm.fees
      WHEN cel.sid IS NOT NULL THEN cel.fees
    END AS fees
  FROM spend s
  LEFT JOIN data_id_fee   dng  ON dng.sid  = s.ng_data
  LEFT JOIN data_id_fee   dng2 ON dng2.sid = s.ng_any
  LEFT JOIN voice_id_fee  vng  ON vng.sid  = s.ng_any
  LEFT JOIN data_name_fee dnm  ON s.norm_detail <> '' AND dnm.name_norm = s.norm_detail
  LEFT JOIN voice_name_fee vnm ON s.norm_detail <> '' AND vnm.name_norm = s.norm_detail
  LEFT JOIN cell_id_fee   cel  ON s.mapped_cell_id IS NOT NULL AND cel.sid = s.mapped_cell_id
)
SELECT
  month_start,
  statement_date,
  sheet_name,
  account_number,
  service_number,
  source,
  source_id,
  statement_category,
  detail_d,
  COALESCE(ng_data, ng_any) AS ng_code,
  amount,
  match_type,
  pb,
  ref,
  fees
FROM matched
WHERE match_type IS NOT NULL
  {_MONTH_FILTER_TOKEN}
ORDER BY month_start NULLS FIRST, sheet_name
"""

# Output columns: (header label, source-row index, kind) where kind ∈ date/text/money.
COLUMNS = [
    ("Statement Date",     1, "date"),
    ("Entity",             2, "text"),
    ("Account Number",     3, "text"),
    ("Service Number",     4, "text"),
    ("Source",             5, "text"),
    ("Source ID",          6, "text"),
    ("Statement Category", 7, "text"),
    ("Detail Description", 8, "text"),
    ("NG Code",            9, "text"),
    ("Amount",            10, "money"),
    ("Type",              11, "text"),
    ("Pricebook",         12, "text"),
    ("Pricebook Cost",    13, "money"),
    ("Discrepancy",       14, "text"),
    ("Difference",        15, "money"),
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def fetch_discrepancies(dsn: str, period: date | None,
                        exclude_categories: "list[str] | None" = None):
    """Return matched spend rows whose billed amount differs from the pricebook cost."""
    if psycopg is None:
        raise RuntimeError("psycopg is not installed; run `pip install psycopg`.")

    if period is None:
        month_filter = ""
    else:
        # period is a datetime.date we build ourselves, so inlining it as a SQL
        # date literal is injection-safe and avoids psycopg treating the many
        # literal '%' characters in the query as parameter placeholders.
        month_filter = f"AND month_start = DATE '{period.isoformat()}'"

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
            raw_rows = cur.fetchall()

    # Raw columns: 0..10 spend fields + amount, 11 match_type, 12 pb, 13 ref, 14 fees[].
    # For each matched row, pick the pricebook fee closest to the billed amount,
    # then keep only rows whose gap is at least the tolerance.
    out = []
    for r in raw_rows:
        amount = float(r[10]) if r[10] is not None else None
        fees = [float(f) for f in (r[14] or []) if f is not None]
        if amount is None or not fees:
            continue
        cost = min(fees, key=lambda f: abs(amount - f))
        diff = amount - cost
        if abs(diff) < COST_TOLERANCE:
            continue
        pricebook = f"{r[12]} ({r[13]})" if r[13] else r[12]
        discrepancy = "higher" if diff > 0 else "lower"
        out.append((
            r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], amount,
            r[11], pricebook, cost, discrepancy, diff,
        ))
    # Worst discrepancies first within each month.
    out.sort(key=lambda x: (x[0] is not None, x[0], -abs(x[15])))
    return out


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


# Excel allows 1,048,576 rows per worksheet; split overflow into continuation tabs.
MAX_DATA_ROWS_PER_SHEET = 1_000_000


def _chunk_tabs(groups: "OrderedDict[str, list]") -> "list[tuple[str, list]]":
    out: "list[tuple[str, list]]" = []
    for tab, rows in groups.items():
        if len(rows) <= MAX_DATA_ROWS_PER_SHEET:
            out.append((tab, rows))
            continue
        for i, start in enumerate(range(0, len(rows), MAX_DATA_ROWS_PER_SHEET), start=1):
            suffix = "" if i == 1 else f" ({i})"
            out.append((f"{tab}{suffix}", rows[start:start + MAX_DATA_ROWS_PER_SHEET]))
    return out


def _col_letter(idx0: int) -> str:
    col = idx0 + 1
    out = ""
    while col:
        col, rem = divmod(col - 1, 26)
        out = chr(65 + rem) + out
    return out


def _apply_widths(ws) -> None:
    widths = [13, 18, 15, 15, 12, 10, 22, 42, 12, 14, 10, 26, 14, 12, 14]
    for idx, w in enumerate(widths):
        ws.set_column(idx, idx, w)


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

    if not groups:
        if single_period is not None:
            groups = OrderedDict({single_period.strftime("%Y-%m"): []})
        else:
            groups = OrderedDict({"No discrepancies": []})

    for tab, rows in _chunk_tabs(groups):
        ws = wb.add_worksheet(_sheet_name(tab))
        # constant_memory mode flushes each row on write, so widths, freeze
        # panes, and the header must be set before the data rows.
        _apply_widths(ws)
        ws.freeze_panes(1, 0)

        for col_idx, (label, _src, _kind) in enumerate(COLUMNS):
            ws.write(0, col_idx, label, header_fmt)

        for out_row, row in enumerate(rows, start=1):
            for col_idx, (_label, src_idx, kind) in enumerate(COLUMNS):
                value = row[src_idx]
                if kind == "date":
                    if value is not None:
                        ws.write_datetime(out_row, col_idx, value, date_fmt)
                    else:
                        ws.write_blank(out_row, col_idx, None, text_fmt)
                elif kind == "money":
                    ws.write_number(out_row, col_idx, float(value or 0), money_fmt)
                else:
                    ws.write(out_row, col_idx, "" if value is None else str(value), text_fmt)

        # Total row (written left-to-right after the data rows to satisfy
        # constant_memory's ordering): label in the first column, SUM formulas
        # under Amount and Difference, blanks elsewhere.
        if rows:
            total_row = len(rows) + 1
            for col_idx, (header, _src, _kind) in enumerate(COLUMNS):
                if col_idx == 0:
                    ws.write(total_row, 0, "Total", total_fmt)
                elif header in ("Amount", "Difference"):
                    letter = _col_letter(col_idx)
                    ws.write_formula(total_row, col_idx,
                                     f"=SUM({letter}2:{letter}{total_row})", total_money_fmt)
                else:
                    ws.write_blank(total_row, col_idx, None, total_fmt)

    wb.close()


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
        description="Validate matched TELUS spend against pricebook cost (one tab per month/year)."
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

    rows = fetch_discrepancies(args.dsn, args.period, exclude_categories)
    groups = group_by_month(rows)
    write_workbook(groups, args.output, args.period)

    total = sum(len(v) for v in groups.values())
    tabs = len(groups) if groups else 0
    scope = args.period.strftime("%Y-%m") if args.period else "all months"
    print(f"✓ {total} cost-discrepancy row(s) across {tabs} tab(s) ({scope}) → {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
