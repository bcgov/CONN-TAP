#!/usr/bin/env python3
"""
Load TSMA / TSMA lite cost Excel workbooks from a folder into Postgres raw tables.

Prereqs:
  pip install -r local_dev/tsma_postgres_ingest/requirements.txt
  psql "$DATABASE_URL" -f local_dev/tsma_postgres_ingest/schema.sql

Usage:
  export DATABASE_URL=postgresql://user:pass@localhost:5432/ngta
  python local_dev/tsma_postgres_ingest/ingest_tsma_excel_folder.py /path/to/excel/root
  python ... /path/to/root --source-period 2025-06-01 --dry-run

Layout (relative to root):
  tsma/wireless/...       -> tsma_wireless
  tsma/wireline/...       -> tsma_wireline
  tsma/master/...         -> tsma_ivr
  tsma_lite/wireless/...  -> tsma_lite_wireless
  tsma_lite/wireline/...  -> tsma_lite_wireline

Recursive by default (.xlsx / .xlsm). One tsma_ingestion_run per file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal, Optional

import pandas as pd
import psycopg

# --- Column lists (must match schema.sql insert column order) ---

TSMA_WIRELESS_COLS = [
    "ingestion_run_id",
    "month_id",
    "month_start_dt",
    "ccyymm",
    "year_num",
    "billg_system_cd",
    "billg_acct_cd",
    "billg_acct_nm",
    "rcid",
    "rcid_cust_nm",
    "cbu_cid",
    "cbucid_cust_nm",
    "lcd_cust_cd",
    "lcd_category",
    "lob",
    "create_dt",
    "total",
    "charge_type",
    "charge_sub_type",
    "lcd_flg",
    "billed_amt",
    "reason_desc",
    "extras",
]

TSMA_WIRELINE_COLS = [
    "ingestion_run_id",
    "month_id",
    "month_start_dt",
    "ccyymm",
    "year_num",
    "lob",
    "lcd_cust_cd",
    "entity",
    "billg_system_cd",
    "rcid",
    "rcid_cust_nm",
    "cbu_cid",
    "cbucid_cust_nm",
    "tsma_spend_ind",
    "data_exclusion_flg",
    "tsma_service_tower",
    "sap_mic_cd_flg",
    "sap_mic_cd",
    "bpi_prod_cd",
    "bpi_prod_desc",
    "prod_family_cd",
    "prod_family_desc",
    "rn_1",
    "rn_2",
    "rn_3",
    "rn_4",
    "epp3_desc",
    "epp3_cd",
    "quantity",
    "billed_amt",
    "line_comment",
    "extras",
]

TSMA_LITE_WIRELINE_COLS = [
    "ingestion_run_id",
    "ccyymm",
    "year_num",
    "rcid",
    "rcid_cust_nm",
    "cbu_cid",
    "cbucid_cust_nm",
    "tsma_spend_ind",
    "data_exclusion_flg",
    "tsma_service_tower",
    "bpi_prod_desc",
    "quantity",
    "billed_amt",
    "extras",
]

TSMA_IVR_COLS = [
    "ingestion_run_id",
    "ccyymm",
    "year_num",
    "rcid",
    "rcid_cust_nm",
    "billed_amt",
    "extras",
]

TSMA_WIRELESS_DB_FIELDS = frozenset(
    c for c in TSMA_WIRELESS_COLS if c not in ("ingestion_run_id", "extras")
)
TSMA_WIRELINE_DB_FIELDS = frozenset(
    c for c in TSMA_WIRELINE_COLS if c not in ("ingestion_run_id", "extras")
)
TSMA_LITE_WIRELINE_DB_FIELDS = frozenset(
    c for c in TSMA_LITE_WIRELINE_COLS if c not in ("ingestion_run_id", "extras")
)
TSMA_IVR_DB_FIELDS = frozenset(c for c in TSMA_IVR_COLS if c not in ("ingestion_run_id", "extras"))

TSMA_WIRELESS_DATES = frozenset(["month_start_dt", "create_dt"])
TSMA_WIRELINE_DATES = frozenset(["month_start_dt"])
TSMA_WIRELESS_INTS = frozenset(["month_id", "year_num"])
TSMA_WIRELINE_INTS = frozenset(["month_id", "year_num"])
TSMA_LITE_WIRELINE_INTS = frozenset(["year_num"])

TSMA_WIRELESS_MONEY = frozenset(["billed_amt"])
TSMA_WIRELINE_MONEY = frozenset(["billed_amt"])
TSMA_LITE_WIRELINE_MONEY = frozenset(["billed_amt"])

TSMA_WIRELINE_NUMERIC = frozenset(["quantity"])
TSMA_LITE_WIRELINE_NUMERIC = frozenset(["quantity"])

FeedCode = Literal[
    "tsma_wireless",
    "tsma_wireline",
    "tsma_lite_wireless",
    "tsma_lite_wireline",
    "tsma_ivr",
]

# Canonical snake (after tsma_header_key) -> schema column when Excel label normalizes oddly.
TSMA_HEADER_REMAP: dict[str, str] = {
    "comment": "line_comment",
    "dataexclusion_flg": "data_exclusion_flg",
    "data_exclusionflg": "data_exclusion_flg",
    "tsma_spendind": "tsma_spend_ind",
    "tsma_servicetower": "tsma_service_tower",
    "sap_mic_cd": "sap_mic_cd",
    "sap_mic_cdflg": "sap_mic_cd_flg",
    "bpi_prod_cd": "bpi_prod_cd",
    "bpi_prod_desc": "bpi_prod_desc",
    "prod_family_cd": "prod_family_cd",
    "prod_family_desc": "prod_family_desc",
    "lcd_flg": "lcd_flg",
    "chargesub_type": "charge_sub_type",
    "rcid_cust_nm": "rcid_cust_nm",
    "cbucid_cust_nm": "cbucid_cust_nm",
    "billg_system_cd": "billg_system_cd",
    "billg_acct_cd": "billg_acct_cd",
    "billg_acct_nm": "billg_acct_nm",
    "month_start_dt": "month_start_dt",
    "create_dt": "create_dt",
    "reason_desc": "reason_desc",
    "epp3_desc": "epp3_desc",
    "epp3_cd": "epp3_cd",
}


def tsma_header_key(name: Any) -> str:
    """Normalize Excel header to snake_case aligned with schema (handles PascalCase/camelCase)."""
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return ""
    s = str(name).replace("\u00a0", " ").strip()
    if not s or s.lower().startswith("unnamed"):
        return ""
    s_compact = re.sub(r"\s+", "", s)
    low_compact = s_compact.casefold()
    if low_compact == "lcd_flg" or low_compact == "lcdflg":
        return "lcd_flg"
    if "dataexclusion" in low_compact and "flg" in low_compact:
        return "data_exclusion_flg"
    if "tsmaspend" in low_compact and "ind" in low_compact:
        return "tsma_spend_ind"
    if "tsmaservice" in low_compact and "tower" in low_compact:
        return "tsma_service_tower"
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s_compact)
    s = re.sub(r"([A-Z])([A-Z][a-z])", r"\1_\2", s)
    s = s.replace(" ", "_").replace("-", "_")
    s = s.lower()
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        return ""
    return TSMA_HEADER_REMAP.get(s, s)


def tsma_db_column(header_key: str, allowed: frozenset[str]) -> str:
    if not header_key:
        return ""
    if header_key in allowed:
        return header_key
    mapped = TSMA_HEADER_REMAP.get(header_key, "")
    if mapped in allowed:
        return mapped
    return ""


def clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(how="all")
    if not df.empty:
        mask_header = df.apply(lambda row: list(row.values) == list(df.columns), axis=1)
        df = df[~mask_header]
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def as_date(val: Any) -> Optional[date]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, pd.Timestamp):
        return val.date() if pd.notna(val) else None
    if isinstance(val, date):
        return val
    ts = pd.to_datetime(val, errors="coerce")
    if pd.isna(ts):
        return None
    return ts.date()


def as_int(val: Any) -> Optional[int]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, int):
        return val
    try:
        s = str(val).strip().replace(",", "")
        if not s:
            return None
        return int(Decimal(s))
    except (InvalidOperation, ValueError):
        return None


def as_text(val: Any) -> Optional[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s else None


def as_money(val: Any) -> Optional[Decimal]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def as_numeric(val: Any) -> Optional[Decimal]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return Decimal(str(val).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def feed_from_path(file_path: Path, root: Path, force: Optional[FeedCode]) -> Optional[FeedCode]:
    if force:
        return force
    try:
        rel = file_path.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    parts = [p.casefold() for p in rel.parts[:-1]]
    if len(parts) < 2:
        return None
    for i in range(len(parts) - 1):
        a, b = parts[i], parts[i + 1]
        if a == "tsma" and b == "wireless":
            return "tsma_wireless"
        if a == "tsma" and b == "wireline":
            return "tsma_wireline"
        if a == "tsma" and b == "master":
            return "tsma_ivr"
        if a == "tsma_lite" and b == "wireless":
            return "tsma_lite_wireless"
        if a == "tsma_lite" and b == "wireline":
            return "tsma_lite_wireline"
    return None


def pick_first_data_sheet(xl: pd.ExcelFile, override: Optional[str]) -> str:
    names = xl.sheet_names
    if override:
        if override not in names:
            raise ValueError(f"Sheet {override!r} not in workbook (have: {names})")
        return override
    for n in names:
        df = pd.read_excel(xl, sheet_name=n, nrows=3, dtype=object)
        if df.empty:
            continue
        if df.dropna(how="all").empty:
            continue
        return n
    return names[0]


def normalize_ccyymm_header(value: Any) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        s = str(int(Decimal(str(value).strip()))).strip()
    except (InvalidOperation, ValueError):
        s = str(value).strip()
    return s if re.fullmatch(r"\d{6}", s) else None


def insert_tsma_ivr_workbook(
    conn: Optional[psycopg.Connection],
    path: Path,
    source_period: Optional[date],
    dry_run: bool,
    sheet: Optional[str],
) -> int:
    sheet_name = sheet or "Pivot - Hosted IVR"
    df = pd.read_excel(path, sheet_name=sheet_name, header=3, dtype=object)
    df = df.dropna(how="all").dropna(axis=1, how="all")
    month_columns = [(col, ccyymm) for col in df.columns if (ccyymm := normalize_ccyymm_header(col))]

    batches = []
    for _, row in df.iterrows():
        rcid_cust_nm = as_text(row.get("RCID_CUST_NM"))
        if not rcid_cust_nm or rcid_cust_nm.casefold() == "grand total":
            continue
        rcid = as_text(row.get("RCID"))
        for month_col, ccyymm in month_columns:
            billed_amt = as_money(row.get(month_col))
            if billed_amt is None:
                continue
            batches.append((None, ccyymm, as_int(ccyymm[:4]), rcid, rcid_cust_nm, billed_amt, None))

    row_total = len(batches)
    if dry_run:
        return row_total
    if conn is None:
        raise ValueError("Postgres connection required unless --dry-run")

    sql = (
        "INSERT INTO tsma_ivr ("
        + ", ".join(TSMA_IVR_COLS)
        + ") VALUES ("
        + ", ".join(["%s"] * len(TSMA_IVR_COLS))
        + ")"
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tsma_ingestion_run (feed_code, source_object_uri, source_period, status)
                VALUES (%s, %s, %s, 'running')
                RETURNING tsma_ingestion_run_id
                """,
                ("tsma_ivr", path.resolve().as_uri(), source_period),
            )
            run_id = cur.fetchone()[0]
            final_rows = []
            for tup in batches:
                lst = list(tup)
                lst[0] = run_id
                final_rows.append(tuple(lst))
            cur.executemany(sql, final_rows)
            cur.execute(
                """
                UPDATE tsma_ingestion_run
                SET finished_at = now(), status = 'completed',
                    row_counts_raw = %s::jsonb
                WHERE tsma_ingestion_run_id = %s
                """,
                (json.dumps({"tsma_ivr": row_total, "sheet": sheet_name}), run_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return row_total


def insert_tsma_workbook(
    conn: Optional[psycopg.Connection],
    path: Path,
    feed: FeedCode,
    source_period: Optional[date],
    dry_run: bool,
    sheet: Optional[str],
) -> int:
    if feed == "tsma_ivr":
        return insert_tsma_ivr_workbook(conn, path, source_period, dry_run, sheet)

    xl = pd.ExcelFile(path)
    sname = pick_first_data_sheet(xl, sheet)
    df = pd.read_excel(xl, sheet_name=sname, dtype=object)
    df = clean_frame(df)
    if df.empty:
        raise ValueError(f"No data in sheet {sname} for {path}")

    if feed in ("tsma_wireless", "tsma_lite_wireless"):
        cols_schema = TSMA_WIRELESS_COLS
        allowed = TSMA_WIRELESS_DB_FIELDS
        dates = TSMA_WIRELESS_DATES
        ints = TSMA_WIRELESS_INTS
        money = TSMA_WIRELESS_MONEY
        numerics: frozenset[str] = frozenset()
        table = "tsma_wireless" if feed == "tsma_wireless" else "tsma_lite_wireless"
    elif feed == "tsma_wireline":
        cols_schema = TSMA_WIRELINE_COLS
        allowed = TSMA_WIRELINE_DB_FIELDS
        dates = TSMA_WIRELINE_DATES
        ints = TSMA_WIRELINE_INTS
        money = TSMA_WIRELINE_MONEY
        numerics = TSMA_WIRELINE_NUMERIC
        table = "tsma_wireline"
    else:
        cols_schema = TSMA_LITE_WIRELINE_COLS
        allowed = TSMA_LITE_WIRELINE_DB_FIELDS
        dates = frozenset()
        ints = TSMA_LITE_WIRELINE_INTS
        money = TSMA_LITE_WIRELINE_MONEY
        numerics = TSMA_LITE_WIRELINE_NUMERIC
        table = "tsma_lite_wireline"

    batches: list[tuple[Any, ...]] = []

    for _, row in df.iterrows():
        vals: dict[str, Any] = {"ingestion_run_id": None}
        extras_payload: dict[str, Any] = {}
        for excel_col in df.columns:
            key = tsma_header_key(excel_col)
            db = tsma_db_column(key, allowed)
            val = row.get(excel_col)
            if db:
                if db in dates:
                    vals[db] = as_date(val)
                elif db in ints:
                    vals[db] = as_int(val)
                elif db in money:
                    vals[db] = as_money(val)
                elif db in numerics:
                    vals[db] = as_numeric(val)
                else:
                    vals[db] = as_text(val)
            elif val is not None and not (isinstance(val, float) and pd.isna(val)):
                extras_payload[str(excel_col)] = (
                    val if isinstance(val, (str, int, float)) else str(val)
                )
        vals["extras"] = json.dumps(extras_payload) if extras_payload else None
        batches.append(tuple(vals.get(c) for c in cols_schema))

    row_total = len(batches)
    if dry_run:
        return row_total
    if conn is None:
        raise ValueError("Postgres connection required unless --dry-run")

    sql = (
        f"INSERT INTO {table} ("
        + ", ".join(cols_schema)
        + ") VALUES ("
        + ", ".join(["%s"] * len(cols_schema))
        + ")"
    )
    counts_key = table
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tsma_ingestion_run (feed_code, source_object_uri, source_period, status)
                VALUES (%s, %s, %s, 'running')
                RETURNING tsma_ingestion_run_id
                """,
                (feed, path.resolve().as_uri(), source_period),
            )
            run_id = cur.fetchone()[0]
            final_rows = []
            for tup in batches:
                lst = list(tup)
                lst[0] = run_id
                final_rows.append(tuple(lst))
            cur.executemany(sql, final_rows)
            cur.execute(
                """
                UPDATE tsma_ingestion_run
                SET finished_at = now(), status = 'completed',
                    row_counts_raw = %s::jsonb
                WHERE tsma_ingestion_run_id = %s
                """,
                (json.dumps({counts_key: row_total, "sheet": sname}), run_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return row_total


def parse_period(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    ts = pd.to_datetime(s, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Invalid --source-period: {s!r}")
    d = ts.date()
    return date(d.year, d.month, 1)


def iter_excel_files(folder: Path, recursive: bool) -> list[Path]:
    patterns = ("*.xlsx", "*.xlsm")
    out: list[Path] = []
    if recursive:
        for pat in patterns:
            out.extend(folder.rglob(pat))
    else:
        for pat in patterns:
            for sub in (
                folder,
                folder / "tsma" / "wireless",
                folder / "tsma" / "wireline",
                folder / "tsma" / "master",
                folder / "tsma_lite" / "wireless",
                folder / "tsma_lite" / "wireline",
            ):
                if sub.is_dir():
                    out.extend(sub.glob(pat))
    return sorted(p for p in out if not p.name.startswith("~$"))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "folder",
        type=Path,
        help="Root directory; workbooks under tsma/{wireless|wireline|master}/ or tsma_lite/...",
    )
    parser.add_argument(
        "--dsn",
        default=os.environ.get("DATABASE_URL"),
        help="Postgres DSN (default: env DATABASE_URL)",
    )
    parser.add_argument(
        "--source-period",
        type=str,
        default=None,
        help="Reporting month as YYYY-MM-DD (first of month stored on tsma_ingestion_run)",
    )
    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Only first-level globs under root and expected tsma/tsma_lite subdirs",
    )
    parser.set_defaults(recursive=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and count rows only; no DATABASE_URL required",
    )
    parser.add_argument(
        "--force-feed",
        choices=(
            "tsma_wireless",
            "tsma_wireline",
            "tsma_ivr",
            "tsma_lite_wireless",
            "tsma_lite_wireline",
        ),
        default=None,
        help="Override path layout: treat every file as this feed",
    )
    parser.add_argument(
        "--sheet",
        default=None,
        help="Excel sheet name (default: first sheet with data, or 'Pivot - Hosted IVR' for tsma/master)",
    )
    args = parser.parse_args(argv)

    if not args.dsn and not args.dry_run:
        print("Set DATABASE_URL or pass --dsn (optional for --dry-run)", file=sys.stderr)
        return 2
    folder = args.folder.expanduser().resolve()
    if not folder.is_dir():
        print(f"Not a directory: {folder}", file=sys.stderr)
        return 2

    period = parse_period(args.source_period)
    files = iter_excel_files(folder, args.recursive)
    if not files:
        print(f"No .xlsx/.xlsm files under {folder}")
        return 0

    force_feed: Optional[FeedCode] = args.force_feed  # type: ignore[assignment]

    totals: dict[str, Any] = {
        "tsma_wireless_files": 0,
        "tsma_wireless_rows": 0,
        "tsma_wireline_files": 0,
        "tsma_wireline_rows": 0,
        "tsma_lite_wireless_files": 0,
        "tsma_lite_wireless_rows": 0,
        "tsma_lite_wireline_files": 0,
        "tsma_lite_wireline_rows": 0,
        "tsma_ivr_files": 0,
        "tsma_ivr_rows": 0,
        "skipped": [],
    }

    def one_file(conn: Optional[psycopg.Connection], path: Path) -> None:
        feed = feed_from_path(path, folder, force_feed)
        if feed is None:
            totals["skipped"].append(str(path))
            print(
                f"[skip] expected path under .../tsma/{{wireless|wireline}}/... or "
                f".../tsma/master/... or .../tsma_lite/{{wireless|wireline}}/... relative to {folder}: {path}",
                file=sys.stderr,
            )
            return
        n = insert_tsma_workbook(conn, path, feed, period, args.dry_run, args.sheet)
        key_base = feed
        totals[f"{key_base}_rows"] += n
        totals[f"{key_base}_files"] += 1
        print(f"[{feed}] {path.name}: {n} rows -> {feed}")

    if args.dry_run:
        for path in files:
            try:
                one_file(None, path)
            except Exception as e:
                print(f"[error] {path.name}: {e}", file=sys.stderr)
                totals["skipped"].append(str(path))
    else:
        with psycopg.connect(args.dsn, autocommit=False) as conn:
            for path in files:
                try:
                    one_file(conn, path)
                except Exception as e:
                    print(f"[error] {path.name}: {e}", file=sys.stderr)
                    conn.rollback()
                    totals["skipped"].append(str(path))

    print(json.dumps(totals, indent=2))
    return 0 if not totals["skipped"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
