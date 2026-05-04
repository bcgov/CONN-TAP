#!/usr/bin/env python3
"""
Load NGTA Telus / Rogers spend Excel workbooks from a folder into Postgres raw tables.

Prereqs:
  pip install -r local_dev/raw_ingestion/ngta_postgres_ingest/requirements.txt
  psql "$DATABASE_URL" -f local_dev/raw_ingestion/ngta_postgres_ingest/schema.sql

Usage:
  export DATABASE_URL=postgresql://user:pass@localhost:5432/ngta
  python local_dev/raw_ingestion/ngta_postgres_ingest/ingest_raw_excel_folder.py /path/to/excel/folder
  python ... /path/to/root --source-period 2025-06-01 --dry-run   # no DATABASE_URL

Layout:
  Telus: place workbooks anywhere under telus/ (any depth), e.g. <root>/telus/*.xlsx.
  Rogers cellular: <root>/rogers/cellular/... -> raw_rogers_spend_cellular.
  Rogers voice + data (one report schema): <root>/rogers/voice/... or <root>/rogers/data/...
  both load into raw_rogers_spend_data_voice (same column mapping). Use one folder or split files across
  voice/ and data/ for convenience; ingestion is identical.
  Files directly under rogers/ are skipped unless --force-provider rogers with --force-rogers-feed
  (cellular|voice). The carrier is taken from path segments telus or rogers (case-insensitive).
  Use --force-provider to override. Recursive by default; --no-recursive limits depth as documented.
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

ROGERS_CELLULAR_COLS = [
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

ROGERS_VOICE_COLS = [
    "ingestion_run_id",
    "bge",
    "sub_bge",
    "accountno",
    "bpso",
    "billingdate",
    "billingperiod_startdate",
    "billingperiod_enddate",
    "circuitno",
    "custrefno",
    "servicestartdate",
    "address",
    "city",
    "province",
    "postalcode",
    "productline",
    "producttype",
    "chargetype",
    "service_id",
    "charge_description",
    "service_component",
    "rate",
    "quantity",
    "consumption",
    "billed_amount_pre_tax",
    "gst",
    "pst",
    "taxamount",
    "totalamount",
    "originating_tn",
    "terminating_tn",
    "destination",
    "destination_country",
    "extras",
]

TELUS_DB_FIELDS = frozenset(c for c in TELUS_COLS if c not in ("ingestion_run_id", "extras", "sheet_name"))
ROGERS_CELLULAR_DB_FIELDS = frozenset(c for c in ROGERS_CELLULAR_COLS if c not in ("ingestion_run_id", "extras"))
ROGERS_VOICE_DB_FIELDS = frozenset(c for c in ROGERS_VOICE_COLS if c not in ("ingestion_run_id", "extras"))

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
    for c in ROGERS_CELLULAR_DB_FIELDS
    if c not in (ROGERS_USAGE | ROGERS_DATES | ROGERS_TEXT | frozenset({"commit_orig_no_month"}))
)

ROGERS_VOICE_DATES = frozenset(
    ["billingdate", "billingperiod_startdate", "billingperiod_enddate", "servicestartdate"]
)

ROGERS_VOICE_MONEY = frozenset(
    ["billed_amount_pre_tax", "gst", "pst", "taxamount", "totalamount"]
)

ROGERS_VOICE_NUMERIC = frozenset(["rate", "quantity", "consumption"])

ROGERS_VOICE_TEXT = frozenset(
    c
    for c in ROGERS_VOICE_DB_FIELDS
    if c
    not in (
        ROGERS_VOICE_DATES | ROGERS_VOICE_MONEY | ROGERS_VOICE_NUMERIC
    )
)

# When canonical_header does not match schema column names, map here (canonical -> voice column).
VOICE_HEADER_CANONICAL_REMAP: dict[str, str] = {
    "account_number": "accountno",
    "account_no": "accountno",
    "account": "accountno",
    "bpso_number": "bpso",
    "billing_date": "billingdate",
    "billing_period_start_date": "billingperiod_startdate",
    "billing_period_startdate": "billingperiod_startdate",
    "billing_period_end_date": "billingperiod_enddate",
    "billing_period_enddate": "billingperiod_enddate",
    "billingperiod_start": "billingperiod_startdate",
    "billingperiod_end": "billingperiod_enddate",
    "service_start_date": "servicestartdate",
    "cust_ref_no": "custrefno",
    "customer_ref_no": "custrefno",
    "circuit_no": "circuitno",
    "postal_code": "postalcode",
    "product_line": "productline",
    "product_type": "producttype",
    "charge_type": "chargetype",
    "charge_desc": "charge_description",
    "charge_description_": "charge_description",
    "service_component_": "service_component",
    "tax_amount": "taxamount",
    "total_amount": "totalamount",
    "originating_tn_": "originating_tn",
    "terminating_tn_": "terminating_tn",
    "destination_country_": "destination_country",
}

TELUS_DATES = frozenset(["statement_date", "due_date"])

RogersFeed = Literal["cellular", "voice"]


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


def voice_db_field(name: Any) -> str:
    ch = canonical_header(name)
    if not ch:
        return ""
    return VOICE_HEADER_CANONICAL_REMAP.get(ch, ch)


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


def pick_rogers_cellular_sheet(xl: pd.ExcelFile, override: Optional[str]) -> str:
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


def pick_rogers_voice_sheet(xl: pd.ExcelFile, override: Optional[str]) -> str:
    names = xl.sheet_names
    if override:
        if override not in names:
            raise ValueError(f"Sheet {override!r} not in workbook (have: {names})")
        return override
    best, best_n = names[0], -1
    need_voice = {"billingdate", "accountno", "circuitno", "custrefno"}
    for n in names:
        df = pd.read_excel(xl, sheet_name=n, nrows=8)
        colset = {voice_db_field(c) for c in df.columns if voice_db_field(c)}
        hit = len(need_voice & colset)
        if hit > best_n:
            best, best_n = n, hit
    if best_n < 1:
        for n in names:
            df = pd.read_excel(xl, sheet_name=n, nrows=3)
            colset = {voice_db_field(c) for c in df.columns if voice_db_field(c)}
            if colset & ROGERS_VOICE_DB_FIELDS:
                return n
        raise ValueError(f"Could not find a Rogers voice-like sheet in {names}")
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


def rogers_feed_from_path(
    root: Path,
    path: Path,
    force_feed: Optional[RogersFeed],
) -> Optional[RogersFeed]:
    """Segment after rogers: cellular -> cellular; voice or data -> voice (same raw table)."""
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return force_feed
    parts = list(rel.parts)
    low = [p.casefold() for p in parts]
    try:
        i = low.index("rogers")
    except ValueError:
        return force_feed
    if i + 1 >= len(parts):
        return force_feed
    seg = low[i + 1]
    if seg == "cellular":
        return "cellular"
    if seg in ("voice", "data"):
        return "voice"
    if i + 1 == len(parts) - 1 and "." in parts[i + 1]:
        return force_feed
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
        f"INSERT INTO {_fq('raw_telus_spend')} ("
        + ", ".join(TELUS_COLS)
        + ") VALUES ("
        + ", ".join(["%s"] * len(TELUS_COLS))
        + ")"
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {_fq('ingestion_run')} (provider, source_object_uri, source_period, status)
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
                f"""
                UPDATE {_fq('ingestion_run')}
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


def insert_rogers_cellular_workbook(
    conn: Optional[psycopg.Connection],
    path: Path,
    source_period: Optional[date],
    dry_run: bool,
    sheet: Optional[str],
) -> int:
    xl = pd.ExcelFile(path)
    sname = pick_rogers_cellular_sheet(xl, sheet)
    df = pd.read_excel(xl, sheet_name=sname, dtype=object)
    df = clean_frame(df)
    if df.empty:
        raise ValueError(f"No data in Rogers cellular sheet {sname} for {path}")

    colmap = {c: canonical_header(c) for c in df.columns}
    batches: list[tuple[Any, ...]] = []

    for _, row in df.iterrows():
        vals: dict[str, Any] = {"ingestion_run_id": None}
        extras_payload: dict[str, Any] = {}
        for excel_col, db in colmap.items():
            if not db:
                continue
            val = row.get(excel_col)
            if db in ROGERS_CELLULAR_DB_FIELDS:
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
        batches.append(tuple(vals.get(c) for c in ROGERS_CELLULAR_COLS))

    row_total = len(batches)
    if dry_run:
        return row_total
    if conn is None:
        raise ValueError("Postgres connection required unless --dry-run")

    sql = (
        f"INSERT INTO {_fq('raw_rogers_spend_cellular')} ("
        + ", ".join(ROGERS_CELLULAR_COLS)
        + ") VALUES ("
        + ", ".join(["%s"] * len(ROGERS_CELLULAR_COLS))
        + ")"
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {_fq('ingestion_run')} (provider, source_object_uri, source_period, status)
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
                f"""
                UPDATE {_fq('ingestion_run')}
                SET finished_at = now(), status = 'completed',
                    row_counts_raw = %s::jsonb
                WHERE ingestion_run_id = %s
                """,
                (json.dumps({"raw_rogers_spend_cellular": row_total, "sheet": sname}), run_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return row_total


def insert_rogers_voice_workbook(
    conn: Optional[psycopg.Connection],
    path: Path,
    source_period: Optional[date],
    dry_run: bool,
    sheet: Optional[str],
) -> int:
    xl = pd.ExcelFile(path)
    sname = pick_rogers_voice_sheet(xl, sheet)
    df = pd.read_excel(xl, sheet_name=sname, dtype=object)
    df = clean_frame(df)
    if df.empty:
        raise ValueError(f"No data in Rogers voice sheet {sname} for {path}")

    colmap = {c: voice_db_field(c) for c in df.columns}
    batches: list[tuple[Any, ...]] = []

    for _, row in df.iterrows():
        vals: dict[str, Any] = {"ingestion_run_id": None}
        extras_payload: dict[str, Any] = {}
        for excel_col, db in colmap.items():
            if not db:
                continue
            val = row.get(excel_col)
            if db in ROGERS_VOICE_DB_FIELDS:
                if db in ROGERS_VOICE_DATES:
                    vals[db] = as_date(val)
                elif db in ROGERS_VOICE_MONEY:
                    vals[db] = as_money(val)
                elif db in ROGERS_VOICE_NUMERIC:
                    vals[db] = as_numeric(val)
                else:
                    vals[db] = as_text(val)
            else:
                if val is not None and not (isinstance(val, float) and pd.isna(val)):
                    extras_payload[str(excel_col)] = (
                        val if isinstance(val, (str, int, float)) else str(val)
                    )
        vals["extras"] = json.dumps(extras_payload) if extras_payload else None
        batches.append(tuple(vals.get(c) for c in ROGERS_VOICE_COLS))

    row_total = len(batches)
    if dry_run:
        return row_total
    if conn is None:
        raise ValueError("Postgres connection required unless --dry-run")

    sql = (
        f"INSERT INTO {_fq('raw_rogers_spend_data_voice')} ("
        + ", ".join(ROGERS_VOICE_COLS)
        + ") VALUES ("
        + ", ".join(["%s"] * len(ROGERS_VOICE_COLS))
        + ")"
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {_fq('ingestion_run')} (provider, source_object_uri, source_period, status)
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
                f"""
                UPDATE {_fq('ingestion_run')}
                SET finished_at = now(), status = 'completed',
                    row_counts_raw = %s::jsonb
                WHERE ingestion_run_id = %s
                """,
                (json.dumps({"raw_rogers_spend_data_voice": row_total, "sheet": sname}), run_id),
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
            telus_dir = folder / "telus"
            if telus_dir.is_dir():
                out.extend(telus_dir.glob(pat))
            for feed in ("cellular", "voice", "data"):
                rdir = folder / "rogers" / feed
                if rdir.is_dir():
                    out.extend(rdir.glob(pat))
    return sorted(p for p in out if not p.name.startswith("~$"))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "folder",
        type=Path,
        help="Root directory; workbooks should live under telus/ and rogers/<feed>/",
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
        help="Only match .xlsx/.xlsm at root, under telus/, and under rogers/cellular|voice|data/ (one level; voice & data dirs both feed raw_rogers_spend_data_voice)",
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
        "--force-rogers-feed",
        choices=("cellular", "voice"),
        default=None,
        help="With --force-provider rogers: cellular vs voice+data long-form (raw_rogers_spend_data_voice)",
    )
    parser.add_argument(
        "--rogers-sheet",
        default=None,
        help="Rogers sheet name (cellular: default Usage_&_Spend or best match; voice+data: best match)",
    )
    args = parser.parse_args(argv)

    if args.force_rogers_feed and args.force_provider != "rogers":
        parser.error("--force-rogers-feed requires --force-provider rogers")

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

    totals: dict[str, Any] = {
        "telus_files": 0,
        "telus_rows": 0,
        "rogers_cellular_files": 0,
        "rogers_cellular_rows": 0,
        "rogers_data_voice_files": 0,
        "rogers_data_voice_rows": 0,
        "skipped": [],
    }

    def one_file(conn: Optional[psycopg.Connection], path: Path) -> None:
        prov = provider_from_folder_path(path, folder, args.force_provider)
        force_feed: Optional[RogersFeed] = args.force_rogers_feed if args.force_provider == "rogers" else None
        feed = rogers_feed_from_path(folder, path, force_feed)

        if prov is None:
            totals["skipped"].append(str(path))
            print(
                f"[skip] expected path under .../telus/... or .../rogers/... relative to {folder}: {path}",
                file=sys.stderr,
            )
            return
        if prov == "rogers" and feed is None:
            totals["skipped"].append(str(path))
            print(
                f"[skip] Rogers file must be under rogers/cellular or rogers/voice or rogers/data "
                f"(or use --force-provider rogers with --force-rogers-feed): {path}",
                file=sys.stderr,
            )
            return
        if prov == "telus":
            n = insert_telus_workbook(conn, path, period, args.dry_run)
            totals["telus_rows"] += n
            totals["telus_files"] += 1
            print(f"[telus] {path.name}: {n} rows -> raw_telus_spend")
            return
        assert feed is not None
        if feed == "cellular":
            n = insert_rogers_cellular_workbook(conn, path, period, args.dry_run, args.rogers_sheet)
            totals["rogers_cellular_rows"] += n
            totals["rogers_cellular_files"] += 1
            print(f"[rogers/cellular] {path.name}: {n} rows -> raw_rogers_spend_cellular")
        else:
            n = insert_rogers_voice_workbook(conn, path, period, args.dry_run, args.rogers_sheet)
            totals["rogers_data_voice_rows"] += n
            totals["rogers_data_voice_files"] += 1
            pl = {p.casefold() for p in path.parts}
            sub = "voice" if "voice" in pl else "data"
            print(f"[rogers/{sub}->voice] {path.name}: {n} rows -> raw_rogers_spend_data_voice")

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
