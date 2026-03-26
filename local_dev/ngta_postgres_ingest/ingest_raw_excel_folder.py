#!/usr/bin/env python3
"""
Load NGTA Telus / Rogers spend Excel workbooks from a folder into Postgres raw tables.

Prereqs:
  pip install -r local_dev/ngta_postgres_ingest/requirements.txt
  psql "$DATABASE_URL" -f local_dev/ngta_postgres_ingest/schema.sql

Usage:
  export DATABASE_URL=postgresql://user:pass@localhost:5432/ngta
  python local_dev/ngta_postgres_ingest/ingest_raw_excel_folder.py /path/to/excel/folder
  python ... /path/to/root --source-period 2025-06-01 --dry-run   # no DATABASE_URL

Layout:
  Under the folder you pass, place workbooks inside subdirectories named telus and rogers
  (case-insensitive), e.g. <root>/telus/*.xlsx and <root>/rogers/*.xlsx. The provider is
  taken from the first path segment under the root that is named telus or rogers.
  Use --force-provider to treat every file as one carrier (override). Deeper subfolders
  under telus/rogers are included by default; use --no-recursive for a shallower scan only.
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

# --- Column lists (must match schema.sql) ---

TELUS_COLS = [
    "ingestion_run_id",
    "sheet_name",
    "account_number",
    "account_description",
    "service_number",
    "statement_date",
    "due_date",
    "statement_section",
    "organization",
    "statement_category",
    "statement_sub_category",
    "record_type_description",
    "amount",
    "bill_section",
    "detail_description",
    "invoice_number",
    "month",
    "service_address",
    "service_description",
    "source",
    "source_id",
    "extras",
]

ROGERS_COLS = [
    "ingestion_run_id",
    "invoice_date",
    "company_code",
    "bge",
    "curr_root_ban",
    "customer_ban",
    "subscriber_no",
    "username",
    "price_plan",
    "plan_description",
    "service_id",
    "data_plan",
    "data_plan_description",
    "service_id_2",
    "init_activation_date",
    "deactivation_date",
    "commit_start_date",
    "commit_end_date",
    "commit_orig_no_month",
    "line_type",
    "dept_code",
    "dept_desc",
    "sim",
    "imei",
    "device",
    "data_overage",
    "sms_domestic",
    "sms_intl",
    "sms_us",
    "ld_intl",
    "ld_us",
    "ecf_data",
    "ecf_voice",
    "hardware",
    "msf_flex_data_options",
    "msf_other_options",
    "msf_other_plans",
    "msf_pool_share_data_options",
    "msf_standalone_data_options",
    "msf_voice_and_data_plan",
    "msf_voice_plan",
    "non_spending_adj",
    "intl_roaming_data",
    "intl_roam_like_home",
    "intl_roaming_addons",
    "roaming_adj",
    "us_roaming_data",
    "us_roam_like_home",
    "us_roaming_addons",
    "push_to_talk",
    "others",
    "billed_amount_pre_tax",
    "gst",
    "pst",
    "hst",
    "qst",
    "billed_amount_post_tax",
    "remaining_device_recovery_fee",
    "voice_domestic_usage",
    "voice_rlh_us_usage",
    "voice_rlh_intl_usage",
    "voice_others_usage",
    "data_domestic_usage",
    "data_rlh_us_usage",
    "data_rlh_intl_usage",
    "data_others_usage",
    "sms_domestic_usage",
    "sms_rlh_us_usage",
    "sms_rlh_intl_usage",
    "sms_others_usage",
    "data_soc",
    "data_soc_description",
    "city",
    "sub_bge",
    "extras",
]

TELUS_DB_FIELDS = frozenset(c for c in TELUS_COLS if c not in ("ingestion_run_id", "extras", "sheet_name"))
ROGERS_DB_FIELDS = frozenset(c for c in ROGERS_COLS if c not in ("ingestion_run_id", "extras"))

ROGERS_USAGE = frozenset(
    [
        "voice_domestic_usage",
        "voice_rlh_us_usage",
        "voice_rlh_intl_usage",
        "voice_others_usage",
        "data_domestic_usage",
        "data_rlh_us_usage",
        "data_rlh_intl_usage",
        "data_others_usage",
        "sms_domestic_usage",
        "sms_rlh_us_usage",
        "sms_rlh_intl_usage",
        "sms_others_usage",
    ]
)

ROGERS_DATES = frozenset(
    [
        "invoice_date",
        "init_activation_date",
        "deactivation_date",
        "commit_start_date",
        "commit_end_date",
    ]
)

ROGERS_TEXT = frozenset(
    [
        "company_code",
        "bge",
        "curr_root_ban",
        "customer_ban",
        "subscriber_no",
        "username",
        "price_plan",
        "plan_description",
        "service_id",
        "data_plan",
        "data_plan_description",
        "service_id_2",
        "line_type",
        "dept_code",
        "dept_desc",
        "sim",
        "imei",
        "device",
        "data_soc",
        "data_soc_description",
        "city",
        "sub_bge",
    ]
)

ROGERS_MONEY = frozenset(
    c
    for c in ROGERS_DB_FIELDS
    if c not in (ROGERS_USAGE | ROGERS_DATES | ROGERS_TEXT | frozenset({"commit_orig_no_month"}))
)

TELUS_DATES = frozenset(["statement_date", "due_date"])


def canonical_header(name: Any) -> str:
    """Map an Excel column label to a snake_case identifier aligned with Postgres columns."""
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return ""
    s = str(name).replace("\u00a0", " ").strip()
    if not s or s.lower().startswith("unnamed"):
        return ""
    s_norm = re.sub(r"\s+", " ", s.lower())
    if s_norm == "sub-bge" or s_norm == "sub bge":
        return "sub_bge"
    # Legacy Rogers reports: CHARGES_SUBTOTAL / CHARGES_TOTAL
    key_snake = re.sub(r"\s+", "_", s_norm)
    if key_snake == "charges_subtotal":
        return "billed_amount_pre_tax"
    if key_snake == "charges_total":
        return "billed_amount_post_tax"
    # POST-TAX before PRE-TAX: plain `"pre" in s` matches inside "post".
    s_compact = (
        s_norm.replace("\u2011", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )
    s_compact = re.sub(r"\s+", "", s_compact)
    if (
        "billed_amount(post-tax)" in s_compact
        or "(post-tax)" in s_compact
        or "billedamount(post-tax)" in s_compact
    ):
        return "billed_amount_post_tax"
    if (
        "billed_amount(pre-tax)" in s_compact
        or "(pre-tax)" in s_compact
        or "billedamount(pre-tax)" in s_compact
    ):
        return "billed_amount_pre_tax"
    s = s.lower().replace(" ", "_").replace("-", "_")
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


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


def as_usage(val: Any) -> Optional[Decimal]:
    return as_numeric(val)


def pick_rogers_sheet(xl: pd.ExcelFile, override: Optional[str]) -> str:
    names = xl.sheet_names
    if override:
        if override not in names:
            raise ValueError(f"Sheet {override!r} not in workbook (have: {names})")
        return override
    if "Usage_&_Spend" in names:
        return "Usage_&_Spend"
    best, best_n = names[0], -1
    need = {"invoice_date", "customer_ban", "subscriber_no"}
    for n in names:
        df = pd.read_excel(xl, sheet_name=n, nrows=5)
        colset = {canonical_header(c) for c in df.columns}
        hit = len(need & colset)
        if hit > best_n:
            best, best_n = n, hit
    if best_n < 2:
        raise ValueError(f"Could not find a Rogers-like sheet in {names}")
    return best


def provider_from_folder_path(
    file_path: Path, root: Path, force: Optional[str]
) -> Optional[Literal["telus", "rogers"]]:
    """Resolve carrier from path: .../<root>/telus/... or .../<root>/rogers/...."""
    if force:
        return force  # type: ignore[return-value]
    try:
        rel = file_path.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    for part in rel.parts[:-1]:
        low = part.casefold()
        if low == "telus":
            return "telus"
        if low == "rogers":
            return "rogers"
    return None


def insert_telus_workbook(
    conn: Optional[psycopg.Connection],
    path: Path,
    source_period: Optional[date],
    dry_run: bool,
) -> int:
    xl = pd.ExcelFile(path)
    batches: list[tuple[Any, ...]] = []

    for sheet_name in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet_name, dtype=object)
        df = clean_frame(df)
        if df.empty:
            continue
        colmap = {c: canonical_header(c) for c in df.columns}
        for _, row in df.iterrows():
            vals: dict[str, Any] = {
                "ingestion_run_id": None,
                "sheet_name": str(sheet_name),
            }
            extras_payload: dict[str, Any] = {}
            for excel_col, db in colmap.items():
                if not db:
                    continue
                val = row.get(excel_col)
                if db in TELUS_DB_FIELDS:
                    if db in TELUS_DATES:
                        vals[db] = as_date(val)
                    elif db == "amount":
                        vals[db] = as_money(val)
                    else:
                        vals[db] = as_text(val)
                else:
                    if val is not None and not (isinstance(val, float) and pd.isna(val)):
                        extras_payload[str(excel_col)] = (
                            val if isinstance(val, (str, int, float)) else str(val)
                        )
            vals["extras"] = json.dumps(extras_payload) if extras_payload else None
            batches.append(tuple(vals.get(c) for c in TELUS_COLS))

    row_total = len(batches)
    if dry_run:
        return row_total
    if conn is None:
        raise ValueError("Postgres connection required unless --dry-run")

    sql = (
        "INSERT INTO raw_telus_spend ("
        + ", ".join(TELUS_COLS)
        + ") VALUES ("
        + ", ".join(["%s"] * len(TELUS_COLS))
        + ")"
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ingestion_run (provider, source_object_uri, source_period, status)
                VALUES (%s, %s, %s, 'running')
                RETURNING ingestion_run_id
                """,
                ("telus", path.resolve().as_uri(), source_period),
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
                UPDATE ingestion_run
                SET finished_at = now(), status = 'completed',
                    row_counts_raw = %s::jsonb
                WHERE ingestion_run_id = %s
                """,
                (json.dumps({"raw_telus_spend": row_total}), run_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return row_total


def insert_rogers_workbook(
    conn: Optional[psycopg.Connection],
    path: Path,
    source_period: Optional[date],
    dry_run: bool,
    sheet: Optional[str],
) -> int:
    xl = pd.ExcelFile(path)
    sname = pick_rogers_sheet(xl, sheet)
    df = pd.read_excel(xl, sheet_name=sname, dtype=object)
    df = clean_frame(df)
    if df.empty:
        raise ValueError(f"No data in Rogers sheet {sname} for {path}")

    colmap = {c: canonical_header(c) for c in df.columns}
    batches: list[tuple[Any, ...]] = []

    for _, row in df.iterrows():
        vals: dict[str, Any] = {"ingestion_run_id": None}
        extras_payload: dict[str, Any] = {}
        for excel_col, db in colmap.items():
            if not db:
                continue
            val = row.get(excel_col)
            if db in ROGERS_DB_FIELDS:
                if db in ROGERS_DATES:
                    vals[db] = as_date(val)
                elif db in ROGERS_USAGE:
                    vals[db] = as_usage(val)
                elif db == "commit_orig_no_month":
                    vals[db] = as_numeric(val)
                elif db in ROGERS_MONEY:
                    vals[db] = as_money(val)
                else:
                    vals[db] = as_text(val)
            else:
                if val is not None and not (isinstance(val, float) and pd.isna(val)):
                    extras_payload[str(excel_col)] = (
                        val if isinstance(val, (str, int, float)) else str(val)
                    )
        vals["extras"] = json.dumps(extras_payload) if extras_payload else None
        batches.append(tuple(vals.get(c) for c in ROGERS_COLS))

    row_total = len(batches)
    if dry_run:
        return row_total
    if conn is None:
        raise ValueError("Postgres connection required unless --dry-run")

    sql = (
        "INSERT INTO raw_rogers_spend ("
        + ", ".join(ROGERS_COLS)
        + ") VALUES ("
        + ", ".join(["%s"] * len(ROGERS_COLS))
        + ")"
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ingestion_run (provider, source_object_uri, source_period, status)
                VALUES (%s, %s, %s, 'running')
                RETURNING ingestion_run_id
                """,
                ("rogers", path.resolve().as_uri(), source_period),
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
                UPDATE ingestion_run
                SET finished_at = now(), status = 'completed',
                    row_counts_raw = %s::jsonb
                WHERE ingestion_run_id = %s
                """,
                (json.dumps({"raw_rogers_spend": row_total, "sheet": sname}), run_id),
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
            out.extend(folder.glob(pat))
            for child in folder.iterdir():
                if child.is_dir() and child.name.casefold() in ("telus", "rogers"):
                    out.extend(child.glob(pat))
    return sorted(p for p in out if not p.name.startswith("~$"))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "folder",
        type=Path,
        help="Root directory; workbooks should live under telus/ and rogers/ subfolders",
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
        help="Reporting month as YYYY-MM-DD (first of month stored on ingestion_run)",
    )
    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Only match .xlsx/.xlsm directly under each carrier folder (no deeper subfolders)",
    )
    parser.set_defaults(recursive=True)
    parser.add_argument("--dry-run", action="store_true", help="Parse and count rows only; no DATABASE_URL required")
    parser.add_argument(
        "--force-provider",
        choices=("telus", "rogers"),
        default=None,
        help="Override folder layout: treat every file as this carrier",
    )
    parser.add_argument(
        "--rogers-sheet",
        default=None,
        help="Rogers sheet name (default: Usage_&_Spend or best-matching sheet)",
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

    totals = {"telus_files": 0, "rogers_files": 0, "telus_rows": 0, "rogers_rows": 0, "skipped": []}

    def one_file(conn: Optional[psycopg.Connection], path: Path) -> None:
        prov = provider_from_folder_path(path, folder, args.force_provider)
        if prov is None:
            totals["skipped"].append(str(path))
            print(
                f"[skip] expected path under .../telus/... or .../rogers/... relative to {folder}: {path}",
                file=sys.stderr,
            )
            return
        if prov == "telus":
            n = insert_telus_workbook(conn, path, period, args.dry_run)
            totals["telus_rows"] += n
            totals["telus_files"] += 1
            print(f"[telus] {path.name}: {n} rows -> raw_telus_spend")
        else:
            n = insert_rogers_workbook(conn, path, period, args.dry_run, args.rogers_sheet)
            totals["rogers_rows"] += n
            totals["rogers_files"] += 1
            print(f"[rogers] {path.name}: {n} rows -> raw_rogers_spend")

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
