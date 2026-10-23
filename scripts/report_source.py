"""Read the spend report's inputs from the dbt report views.

The workbook builders read these views directly; there are no exported CSVs or report
SQL files. The views read raw data live, so a newly ingested month is included without
publishing anything, but they must exist and be current:

    dbt run --select staging intermediate

Connection: env DATABASE_URL, else the local docker database.

Snapshot (for layout / formatting work): set SPEND_REPORT_SNAPSHOT=1 and each query's
result is saved to scripts/source/report_snapshot/ the first time, then read from there
on later builds -- no database needed, but the data is frozen. Delete the folder (or unset
the variable) to go back to live data.
"""

from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

DEFAULT_DSN = "postgresql://app:app@localhost:5432/app"
SNAPSHOT_DIR = Path(__file__).parent / "source" / "report_snapshot"


@lru_cache(maxsize=None)
def view_rows(query: str) -> tuple[dict[str, str], ...]:
    """Run a read-only query against the report views.

    Values come back as text ('' for NULL), the same shape the loaders used to read
    from CSV. Cached per query, so a view read by two loaders is computed once per build.
    """
    snapshot = None
    if os.environ.get("SPEND_REPORT_SNAPSHOT"):
        snapshot = SNAPSHOT_DIR / f"{hashlib.sha1(query.encode()).hexdigest()[:12]}.json"
        if snapshot.exists():
            return tuple(json.loads(snapshot.read_text())["rows"])

    with psycopg.connect(os.environ.get("DATABASE_URL", DEFAULT_DSN)) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query)
            rows = tuple(
                {k: "" if v is None else str(v) for k, v in row.items()}
                for row in cur.fetchall()
            )

    if snapshot is not None:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        snapshot.write_text(json.dumps({"query": query, "rows": rows}))
    return rows
