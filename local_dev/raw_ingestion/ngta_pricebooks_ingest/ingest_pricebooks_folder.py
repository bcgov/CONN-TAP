#!/usr/bin/env python3
"""
Load NGTA Rogers / Telus pricebooks from a folder into Postgres raw tables.

Prereqs:
  pip install -r local_dev/raw_ingestion/ngta_pricebooks_ingest/requirements.txt
  cd app/backend && alembic upgrade head   # creates raw_data (see alembic/raw_data/ngta_pricebooks.sql)

Usage:
  export DATABASE_URL=postgresql://user:pass@localhost:5432/ngta
  python local_dev/raw_ingestion/ngta_pricebooks_ingest/ingest_pricebooks_folder.py /path/to/price_books
  python ... /path/to/price_books --dry-run

Layout (files are not committed; place locally):
  Rogers (PDF under price_books/rogers/):
    professional_services.pdf, data.pdf, cellular.pdf, voice.pdf
  Telus (Excel under price_books/telus/):
    u_ngta_cellular_additional_fees_catalogue.xlsx, u_ngta_cellular_services_catalogue.xlsx, ...

Carrier is inferred from path segments rogers or telus (case-insensitive).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

import psycopg

_PKG_ROOT = Path(__file__).resolve().parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from common import Provider, iter_pricebook_files, parse_period, provider_from_path  # noqa: E402
from rogers import process_pdf as process_rogers_pdf  # noqa: E402
from telus import process_file as process_telus_file  # noqa: E402

_EXCEL_SUFFIXES = frozenset({".xlsx", ".xlsm"})


def process_path(
    conn: Optional[psycopg.Connection],
    path: Path,
    *,
    root: Path,
    period: Optional[date],
    force_provider: Optional[Provider],
    dry_run: bool,
) -> tuple[int, str]:
    prov = provider_from_path(path, root, force_provider)
    if prov is None:
        raise ValueError(
            f"Expected path under .../rogers/... or .../telus/... relative to {root}: {path}"
        )
    suffix = path.suffix.casefold()
    if prov == "rogers":
        if suffix != ".pdf":
            raise ValueError(f"Rogers pricebooks must be PDF, got {path.name!r}")
        return process_rogers_pdf(conn, path, source_period=period, dry_run=dry_run)
    if suffix not in _EXCEL_SUFFIXES:
        raise ValueError(f"Telus pricebooks must be Excel (.xlsx), got {path.name!r}")
    return process_telus_file(conn, path, source_period=period, dry_run=dry_run)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "folder",
        type=Path,
        help="Root directory containing rogers/ and telus/ pricebook files",
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
        help="Effective period as YYYY-MM-DD (stored on pricebook_ingestion_run)",
    )
    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Only match files at root and one level under rogers/ or telus/",
    )
    parser.set_defaults(recursive=True)
    parser.add_argument("--dry-run", action="store_true", help="Parse and count rows only")
    parser.add_argument(
        "--force-provider",
        choices=("telus", "rogers"),
        default=None,
        help="Override carrier inferred from folder path",
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
    files = iter_pricebook_files(folder, args.recursive)
    if not files:
        print(f"No pricebook files (.pdf / .xlsx) under {folder}")
        return 0

    totals: dict[str, Any] = {"files": 0, "rows": 0, "by_table": {}, "skipped": []}

    for path in files:
        try:
            if args.dry_run:
                n, table = process_path(
                    None,
                    path,
                    root=folder,
                    period=period,
                    force_provider=args.force_provider,
                    dry_run=True,
                )
            else:
                with psycopg.connect(args.dsn, autocommit=False) as conn:
                    n, table = process_path(
                        conn,
                        path,
                        root=folder,
                        period=period,
                        force_provider=args.force_provider,
                        dry_run=False,
                    )
            totals["files"] += 1
            totals["rows"] += n
            totals["by_table"][table] = totals["by_table"].get(table, 0) + n
            print(f"[ok] {path.name}: {n} rows -> {table}")
        except NotImplementedError as e:
            totals["skipped"].append(str(path))
            print(f"[skip] {path.name}: {e}", file=sys.stderr)
        except Exception as e:
            totals["skipped"].append(str(path))
            print(f"[error] {path.name}: {e}", file=sys.stderr)

    print(json.dumps(totals, indent=2))
    return 0 if not totals["skipped"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
