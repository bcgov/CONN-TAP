#!/usr/bin/env python3
"""
Load TSMA Other Excel workbooks (managed security, router) into Postgres.

WLAN / Wi‑Fi wireline-shaped extracts belong in ``tsma/wireline/`` and ``raw_data.tsma_wireline`` via
``ingest_tsma_excel_folder.py``, not this script.

Prereqs:
  pip install -r local_dev/raw_ingestion/tsma_other_postgres_ingest/requirements.txt
  psql "$DATABASE_URL" -f local_dev/raw_ingestion/tsma_other_postgres_ingest/schema.sql

Usage:
  export DATABASE_URL=postgresql://user:pass@localhost:5432/ngta
  python local_dev/raw_ingestion/tsma_other_postgres_ingest/ingest_tsma_other_excel_folder.py /path/to/tsma_other
  python ... /path/to/tsma_other --source-period 2025-06-01 --dry-run

Layout: pass the ``tsma_other`` directory. It may contain these subfolders, each with one or
more ``.xlsx`` / ``.xlsm`` files directly inside (not nested paths):

  tsma_other/managed_security/   -> tsma_other_managed_security
  tsma_other/managed_router/     -> tsma_other_managed_router

One ``tsma_other_ingestion_run`` row per workbook file.
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

PG_SCHEMA = "raw_data"


def _fq(ident: str) -> str:
    return f"{PG_SCHEMA}.{ident}"


# Wireline-shaped columns (must match schema.sql insert order).
ROW_COLS = [
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

ROW_DB_FIELDS = frozenset(c for c in ROW_COLS if c not in ("ingestion_run_id", "extras"))
ROW_DATES = frozenset(["month_start_dt"])
ROW_INTS = frozenset(["month_id", "year_num"])
ROW_MONEY = frozenset(["billed_amt"])
ROW_NUMERIC = frozenset(["rn_1", "rn_2", "rn_3", "rn_4", "quantity"])

FeedCode = Literal[
    "tsma_other_managed_security",
    "tsma_other_managed_router",
]

SUBFOLDER_TO_FEED: dict[str, FeedCode] = {
    "managed_security": "tsma_other_managed_security",
    "managed_router": "tsma_other_managed_router",
}

FEED_TO_TABLE: dict[FeedCode, str] = {
    "tsma_other_managed_security": "tsma_other_managed_security",
    "tsma_other_managed_router": "tsma_other_managed_router",
}

HEADER_REMAP: dict[str, str] = {
    "total": "total_amt",
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
    "rcid_cust_nm": "rcid_cust_nm",
    "cbucid_cust_nm": "cbucid_cust_nm",
    "billg_system_cd": "billg_system_cd",
    "month_start_dt": "month_start_dt",
    "epp3_desc": "epp3_desc",
    "epp3_cd": "epp3_cd",
}


def header_key(name: Any) -> str:
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
    return HEADER_REMAP.get(s, s)


def db_column(header_key_val: str, allowed: frozenset[str]) -> str:
    if not header_key_val:
        return ""
    if header_key_val in allowed:
        return header_key_val
    mapped = HEADER_REMAP.get(header_key_val, "")
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


def excel_files_direct(subdir: Path) -> list[Path]:
    if not subdir.is_dir():
        return []
    out: list[Path] = []
    for pat in ("*.xlsx", "*.xlsm"):
        out.extend(subdir.glob(pat))
    return sorted(p for p in out if not p.name.startswith("~$"))


def discover_jobs(tsma_other_root: Path) -> list[tuple[Path, FeedCode]]:
    jobs: list[tuple[Path, FeedCode]] = []
    for sub_name, feed in SUBFOLDER_TO_FEED.items():
        d = tsma_other_root / sub_name
        for path in excel_files_direct(d):
            jobs.append((path, feed))  # type: ignore[arg-type]
    return sorted(jobs, key=lambda x: (str(x[0].parent), str(x[0])))


def insert_workbook(
    conn: Optional[psycopg.Connection],
    path: Path,
    feed: FeedCode,
    source_period: Optional[date],
    dry_run: bool,
    sheet: Optional[str],
) -> int:
    table = FEED_TO_TABLE[feed]
    xl = pd.ExcelFile(path)
    sname = pick_first_data_sheet(xl, sheet)
    df = pd.read_excel(xl, sheet_name=sname, dtype=object)
    df = clean_frame(df)
    if df.empty:
        raise ValueError(f"No data in sheet {sname} for {path}")

    batches: list[tuple[Any, ...]] = []
    for _, row in df.iterrows():
        vals: dict[str, Any] = {"ingestion_run_id": None}
        extras_payload: dict[str, Any] = {}
        for excel_col in df.columns:
            key = header_key(excel_col)
            col = db_column(key, ROW_DB_FIELDS)
            val = row.get(excel_col)
            if col:
                if col in ROW_DATES:
                    vals[col] = as_date(val)
                elif col in ROW_INTS:
                    vals[col] = as_int(val)
                elif col in ROW_MONEY:
                    vals[col] = as_money(val)
                elif col in ROW_NUMERIC:
                    vals[col] = as_numeric(val)
                else:
                    vals[col] = as_text(val)
            elif val is not None and not (isinstance(val, float) and pd.isna(val)):
                extras_payload[str(excel_col)] = (
                    val if isinstance(val, (str, int, float)) else str(val)
                )
        vals["extras"] = json.dumps(extras_payload) if extras_payload else None
        batches.append(tuple(vals.get(c) for c in ROW_COLS))

    row_total = len(batches)
    if dry_run:
        return row_total
    if conn is None:
        raise ValueError("Postgres connection required unless --dry-run")

    sql = (
        f"INSERT INTO {_fq(table)} ("
        + ", ".join(ROW_COLS)
        + ") VALUES ("
        + ", ".join(["%s"] * len(ROW_COLS))
        + ")"
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {_fq('tsma_other_ingestion_run')} (feed_code, source_object_uri, source_period, status)
                VALUES (%s, %s, %s, 'running')
                RETURNING tsma_other_ingestion_run_id
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
                f"""
                UPDATE {_fq('tsma_other_ingestion_run')}
                SET finished_at = now(), status = 'completed',
                    row_counts_raw = %s::jsonb
                WHERE tsma_other_ingestion_run_id = %s
                """,
                (json.dumps({table: row_total, "sheet": sname}), run_id),
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


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "folder",
        type=Path,
        help="Path to tsma_other (contains managed_security, managed_router)",
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
        help="Reporting month YYYY-MM-DD (first of month on tsma_other_ingestion_run)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and count rows only; no DATABASE_URL required",
    )
    parser.add_argument(
        "--sheet",
        default=None,
        help="Excel sheet name (default: first sheet with data)",
    )
    args = parser.parse_args(argv)

    if not args.dsn and not args.dry_run:
        print("Set DATABASE_URL or pass --dsn (optional for --dry-run)", file=sys.stderr)
        return 2

    root = args.folder.expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    period = parse_period(args.source_period)
    jobs = discover_jobs(root)
    if not jobs:
        print(
            f"No .xlsx/.xlsm files directly under {root}/managed_security or {root}/managed_router",
            file=sys.stderr,
        )
        return 0

    totals: dict[str, Any] = {
        "tsma_other_managed_security_files": 0,
        "tsma_other_managed_security_rows": 0,
        "tsma_other_managed_router_files": 0,
        "tsma_other_managed_router_rows": 0,
        "skipped": [],
    }

    def run_job(conn: Optional[psycopg.Connection], path: Path, feed: FeedCode) -> None:
        n = insert_workbook(conn, path, feed, period, args.dry_run, args.sheet)
        totals[f"{feed}_rows"] += n
        totals[f"{feed}_files"] += 1
        print(f"[{feed}] {path.name}: {n} rows -> {FEED_TO_TABLE[feed]}")

    if args.dry_run:
        for path, feed in jobs:
            try:
                run_job(None, path, feed)
            except Exception as e:
                print(f"[error] {path}: {e}", file=sys.stderr)
                totals["skipped"].append(str(path))
    else:
        with psycopg.connect(args.dsn, autocommit=False) as conn:
            for path, feed in jobs:
                try:
                    run_job(conn, path, feed)
                except Exception as e:
                    print(f"[error] {path}: {e}", file=sys.stderr)
                    conn.rollback()
                    totals["skipped"].append(str(path))

    print(json.dumps(totals, indent=2))
    return 0 if not totals["skipped"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
