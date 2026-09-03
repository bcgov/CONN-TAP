"""Load Telus pricebook v2 Excel workbooks into Postgres raw tables.

Unlike the old telus/ingest.py (one file -> one table), a v2 workbook fans
out into several tables (one per sheet), all recorded under a single
pricebook_ingestion_run row keyed by the book code (e.g.
"cellular_services_v2"), with row_counts_raw capturing per-table counts.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

import psycopg

from common import fq
from telus_v2.catalogues import SplitByValueSheetSpec, resolve_book
from telus_v2.excel import parse_workbook

# New v2 tables live in their own schema, separate from raw_data (where
# pricebook_ingestion_run and the original raw_telus_* tables stay).
_PG_SCHEMA_V2 = "raw_data_v2"


def _fq_v2(table_name: str) -> str:
    return f"{_PG_SCHEMA_V2}.{table_name}"


def _insert_columns(spec_columns: tuple[str, ...]) -> list[str]:
    return ["pricebook_ingestion_run_id", "excel_row_number", *spec_columns, "extras"]


def process_file(
    conn: Optional[psycopg.Connection],
    path: Path,
    *,
    source_period: Optional[date],
    dry_run: bool,
) -> tuple[int, str]:
    book = resolve_book(path.stem)
    rows_by_table = parse_workbook(path, book)
    for table_name, rows in rows_by_table.items():
        if not rows:
            raise ValueError(f"No data rows extracted from {path} for {table_name}")

    table_columns: dict[str, tuple[str, ...]] = {}
    for spec in book.sheets:
        if isinstance(spec, SplitByValueSheetSpec):
            for table_name in spec.table_by_value.values():
                table_columns[table_name] = spec.columns
        else:
            table_columns[spec.table_name] = spec.columns
    row_total = sum(len(rows) for rows in rows_by_table.values())

    if dry_run:
        return row_total, book.book_code
    if conn is None:
        raise ValueError("Postgres connection required unless --dry-run")

    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {fq('pricebook_ingestion_run')}
                  (provider, pricebook_feed, source_object_uri, source_period, status)
                VALUES (%s, %s, %s, %s, 'running')
                RETURNING pricebook_ingestion_run_id
                """,
                ("telus", book.book_code, path.resolve().as_uri(), source_period),
            )
            run_id = cur.fetchone()[0]

            row_counts: dict[str, int] = {}
            for table_name, rows in rows_by_table.items():
                columns = _insert_columns(table_columns[table_name])
                sql = (
                    f"INSERT INTO {_fq_v2(table_name)} ("
                    + ", ".join(columns)
                    + ") VALUES ("
                    + ", ".join(["%s"] * len(columns))
                    + ")"
                )
                batches = []
                for row in rows:
                    row = dict(row)
                    row["pricebook_ingestion_run_id"] = run_id
                    batches.append(tuple(row.get(c) for c in columns))
                cur.executemany(sql, batches)
                row_counts[table_name] = len(rows)

            cur.execute(
                f"""
                UPDATE {fq('pricebook_ingestion_run')}
                SET finished_at = now(), status = 'completed',
                    row_counts_raw = %s::jsonb
                WHERE pricebook_ingestion_run_id = %s
                """,
                (json.dumps(row_counts), run_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return row_total, book.book_code
