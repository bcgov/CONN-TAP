"""Load Rogers pricebook PDFs into Postgres raw tables."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any, Literal, Optional

import psycopg

from common import fq
from rogers.parsers import (
    CELLULAR_COLUMNS,
    DATA_COLUMNS,
    PROFESSIONAL_SERVICES_COLUMNS,
    VOICE_COLUMNS,
    parse_rogers_cellular_pdf,
    parse_rogers_data_pdf,
    parse_rogers_professional_services_pdf,
    parse_rogers_voice_pdf,
)

RogersFeed = Literal["professional_services", "cellular", "data", "voice"]

FEED_FILENAMES: dict[RogersFeed, str] = {
    "professional_services": "professional_services.pdf",
    "cellular": "cellular.pdf",
    "data": "data.pdf",
    "voice": "voice.pdf",
}

_FEED_HANDLERS: dict[
    RogersFeed,
    tuple[str, list[str], Callable[[Path], list[dict[str, Any]]], str],
] = {
    "professional_services": (
        "raw_rogers_professional_services_pricebook",
        PROFESSIONAL_SERVICES_COLUMNS,
        parse_rogers_professional_services_pdf,
        "raw_rogers_professional_services_pricebook",
    ),
    "data": (
        "raw_rogers_data_pricebook",
        DATA_COLUMNS,
        parse_rogers_data_pdf,
        "raw_rogers_data_pricebook",
    ),
    "cellular": (
        "raw_rogers_cellular_pricebook",
        CELLULAR_COLUMNS,
        parse_rogers_cellular_pdf,
        "raw_rogers_cellular_pricebook",
    ),
    "voice": (
        "raw_rogers_voice_pricebook",
        VOICE_COLUMNS,
        parse_rogers_voice_pdf,
        "raw_rogers_voice_pricebook",
    ),
}


def feed_from_filename(path: Path) -> Optional[RogersFeed]:
    name = path.name.casefold()
    for feed, expected in FEED_FILENAMES.items():
        if name == expected.casefold():
            return feed
    stem = path.stem.casefold()
    if stem in FEED_FILENAMES:
        return stem  # type: ignore[return-value]
    return None


def _insert_pdf(
    conn: Optional[psycopg.Connection],
    path: Path,
    source_period: Optional[date],
    dry_run: bool,
    *,
    feed: RogersFeed,
    table_name: str,
    columns: list[str],
    parse_pdf: Callable[[Path], list[dict[str, Any]]],
    row_count_key: str,
) -> int:
    parsed = parse_pdf(path)
    if not parsed:
        raise ValueError(f"No data rows extracted from {path}")

    batches = [tuple(row.get(c) for c in columns) for row in parsed]
    row_total = len(batches)
    if dry_run:
        return row_total
    if conn is None:
        raise ValueError("Postgres connection required unless --dry-run")

    sql = (
        f"INSERT INTO {fq(table_name)} ("
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
                ("rogers", feed, path.resolve().as_uri(), source_period),
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
                (json.dumps({row_count_key: row_total}), run_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return row_total


def process_pdf(
    conn: Optional[psycopg.Connection],
    path: Path,
    *,
    source_period: Optional[date],
    dry_run: bool,
) -> tuple[int, str]:
    feed = feed_from_filename(path)
    if feed is None:
        raise ValueError(
            f"Unknown Rogers pricebook file {path.name!r}; expected one of: "
            + ", ".join(FEED_FILENAMES.values())
        )
    table_name, columns, parse_pdf, row_count_key = _FEED_HANDLERS[feed]
    n = _insert_pdf(
        conn,
        path,
        source_period,
        dry_run,
        feed=feed,
        table_name=table_name,
        columns=columns,
        parse_pdf=parse_pdf,
        row_count_key=row_count_key,
    )
    return n, table_name
