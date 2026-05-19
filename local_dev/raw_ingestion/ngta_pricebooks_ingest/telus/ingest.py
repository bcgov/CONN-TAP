"""Load Telus pricebook Excel catalogues into Postgres raw tables."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Optional

import psycopg

from common import fq
from telus.catalogues import resolve_catalogue
from telus.excel import parse_workbook


def _insert_columns(spec_columns: tuple[str, ...]) -> list[str]:
    return ["pricebook_ingestion_run_id", "sheet_name", *spec_columns, "extras"]


def process_file(
    conn: Optional[psycopg.Connection],
    path: Path,
    *,
    source_period: Optional[date],
    dry_run: bool,
) -> tuple[int, str]:
    spec = resolve_catalogue(path.stem)
    parsed = parse_workbook(path, spec)
    if not parsed:
        raise ValueError(f"No data rows extracted from {path}")

    columns = _insert_columns(spec.columns)
    batches = [tuple(row.get(c) for c in columns) for row in parsed]
    row_total = len(batches)
    if dry_run:
        return row_total, spec.table_name
    if conn is None:
        raise ValueError("Postgres connection required unless --dry-run")

    sql = (
        f"INSERT INTO {fq(spec.table_name)} ("
        + ", ".join(columns)
        + ") VALUES ("
        + ", ".join(["%s"] * len(columns))
        + ")"
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {fq('pricebook_ingestion_run')}
                  (provider, pricebook_feed, source_object_uri, source_period, status)
                VALUES (%s, %s, %s, %s, 'running')
                RETURNING pricebook_ingestion_run_id
                """,
                ("telus", spec.feed_code, path.resolve().as_uri(), source_period),
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
                UPDATE {fq('pricebook_ingestion_run')}
                SET finished_at = now(), status = 'completed',
                    row_counts_raw = %s::jsonb
                WHERE pricebook_ingestion_run_id = %s
                """,
                (json.dumps({spec.table_name: row_total}), run_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return row_total, spec.table_name
