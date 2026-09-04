#!/usr/bin/env python3
"""
Load NGTA pricebook v2 workbooks from a folder into Postgres raw tables.

The v2 price books are single-workbook Excel files (one sheet per
catalogue), replacing the old one-file-per-catalogue layout handled by
ingest_pricebooks_folder.py / telus/ / rogers/. This is a sibling script for
that new format only — it does not touch the existing telus/rogers ingestion.

Provider is inferred from a filename prefix: Telus sends "TCI ..." (e.g.
"TCI NGTA Price Book Cellular Services v2.0.xlsx"), Rogers sends "RCCI ..."
(RCCI = Rogers Communications Canada Inc., e.g.
"RCCI NGTA Price Book Cellular Services v1.2.xlsx"). Both providers use the
same "Cellular Services" sheet name and "cellular services"/"devices
catalogue" file_match substrings, so the provider prefix has to be checked
first — each provider's BookSpec.file_match is only resolved within its own
BOOKS list, never across both.

Prereqs:
  pip install -r local_dev/raw_ingestion/ngta_pricebooks_ingest/requirements.txt
  cd app/backend && alembic upgrade head   # creates the raw_data_v2 schema and its
                                            # raw_telus_v2_* / raw_rogers_v2_* tables
                                            # (see alembic/raw_data/ngta_pricebooks_v2.sql)

Usage:
  export DATABASE_URL=postgresql://user:pass@localhost:5432/ngta
  python local_dev/raw_ingestion/ngta_pricebooks_ingest/ingest_pricebooks_v2_folder.py /path/to/price_books_v2
  python ... /path/to/price_books_v2 --dry-run

Layout (files are not committed; place locally):
  price_books_v2/
    TCI NGTA Price Book Cellular Services v2.0.xlsx
    RCCI NGTA Price Book Cellular Services v1.2.xlsx
    ... (more books as they're added; see telus_v2/catalogues.py and
    rogers_v2/catalogues.py BOOKS)

The book is inferred from the filename (see BookSpec.file_match in
telus_v2/catalogues.py or rogers_v2/catalogues.py); it does not need to sit
under a rogers/telus subdir.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, Callable, Optional

import psycopg

_PKG_ROOT = Path(__file__).resolve().parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from common import parse_period  # noqa: E402
from rogers_v2 import process_file as process_rogers_v2_file  # noqa: E402
from telus_v2 import process_file as process_telus_v2_file  # noqa: E402

_EXCEL_SUFFIXES = frozenset({".xlsx", ".xlsm"})

ProcessFn = Callable[..., tuple[int, str]]


def resolve_processor(path: Path) -> ProcessFn:
    stem = path.stem.casefold()
    if "rcci" in stem:
        return process_rogers_v2_file
    if "tci" in stem:
        return process_telus_v2_file
    raise ValueError(
        f"{path.name}: can't tell provider from filename; expected a 'TCI' (Telus) or 'RCCI' (Rogers) prefix"
    )


def iter_workbook_files(folder: Path) -> list[Path]:
    paths: list[Path] = []
    for pat in ("*.xlsx", "*.xlsm"):
        paths.extend(folder.glob(pat))
    return sorted(p for p in paths if not p.name.startswith("~$") and not p.name.startswith("."))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, help="Directory containing v2 pricebook .xlsx files")
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
    parser.add_argument("--dry-run", action="store_true", help="Parse and count rows only")
    args = parser.parse_args(argv)

    if not args.dsn and not args.dry_run:
        print("Set DATABASE_URL or pass --dsn (optional for --dry-run)", file=sys.stderr)
        return 2

    folder = args.folder.expanduser().resolve()
    if not folder.is_dir():
        print(f"Not a directory: {folder}", file=sys.stderr)
        return 2

    period = parse_period(args.source_period)
    files = iter_workbook_files(folder)
    if not files:
        print(f"No .xlsx/.xlsm pricebook files under {folder}")
        return 0

    totals: dict[str, Any] = {"files": 0, "rows": 0, "by_book": {}, "skipped": []}

    for path in files:
        try:
            process_file = resolve_processor(path)
            if args.dry_run:
                n, book = process_file(None, path, source_period=period, dry_run=True)
            else:
                with psycopg.connect(args.dsn, autocommit=False) as conn:
                    n, book = process_file(conn, path, source_period=period, dry_run=False)
            totals["files"] += 1
            totals["rows"] += n
            totals["by_book"][book] = totals["by_book"].get(book, 0) + n
            print(f"[ok] {path.name}: {n} rows -> book {book}")
        except Exception as e:
            totals["skipped"].append(str(path))
            print(f"[error] {path.name}: {e}", file=sys.stderr)

    print(json.dumps(totals, indent=2))
    return 0 if not totals["skipped"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
