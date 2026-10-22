"""Read the spend report's inputs from the dbt report views.

The workbook builders read these views directly; there are no exported CSVs or report
SQL files. The views read raw data live, so a newly ingested month is included without
publishing anything, but they must exist and be current:

    dbt run --select staging intermediate

Connection: env DATABASE_URL, else the local docker database.
"""

from __future__ import annotations

import os
from functools import lru_cache

import psycopg
from psycopg.rows import dict_row

DEFAULT_DSN = "postgresql://app:app@localhost:5432/app"


@lru_cache(maxsize=None)
def view_rows(query: str) -> tuple[dict[str, str], ...]:
    """Run a read-only query against the report views.

    Values come back as text ('' for NULL), the same shape the loaders used to read
    from CSV. Cached per query, so a view read by two loaders is computed once per build.
    """
    with psycopg.connect(os.environ.get("DATABASE_URL", DEFAULT_DSN)) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query)
            return tuple(
                {k: "" if v is None else str(v) for k, v in row.items()}
                for row in cur.fetchall()
            )
