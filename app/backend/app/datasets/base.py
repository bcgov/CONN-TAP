"""Base classes and helpers shared by all dataset modules."""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class DatasetResult:
    """Standard envelope returned to the API layer."""

    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, metadata: dict[str, Any] | None = None) -> "DatasetResult":
        return cls(
            columns=list(df.columns),
            rows=df.where(pd.notnull(df), None).values.tolist(),
            row_count=int(len(df)),
            metadata=metadata or {},
        )


_QUERY_RE = re.compile(r"^\s*--\s*name:\s*(\S+)\s*$", re.IGNORECASE)


def parse_named_queries(sql_path: Path) -> dict[str, str]:
    """Parse a SQL file into a dict of `{name: sql}`.

    Format::

        -- name: list_all
        SELECT ...;

        -- name: by_region
        SELECT ... WHERE region = :region;
    """
    if not sql_path.exists():
        return {}

    queries: dict[str, list[str]] = {}
    current: str | None = None

    for line in sql_path.read_text(encoding="utf-8").splitlines():
        match = _QUERY_RE.match(line)
        if match:
            current = match.group(1)
            queries[current] = []
            continue
        if current is not None:
            queries[current].append(line)

    return {name: "\n".join(lines).strip().rstrip(";") for name, lines in queries.items()}


def load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


class DatasetService(ABC):
    """Subclass this in each dataset's `service.py`.

    Subclasses must define `id` (used in URLs) and implement `run`.
    """

    id: ClassVar[str]
    name: ClassVar[str] = ""
    description: ClassVar[str] = ""

    #: Path to the dataset's directory. Set by the registry.
    module_dir: Path
    config: dict[str, Any]
    queries: dict[str, str]

    def __init__(self, module_dir: Path) -> None:
        self.module_dir = module_dir
        self.config = load_config(module_dir / "config.json")
        self.queries = parse_named_queries(module_dir / "queries.sql")

        # Allow config.json to override class-level metadata.
        if not self.name:
            self.name = self.config.get("name", self.id)
        if not self.description:
            self.description = self.config.get("description", "")

    # ---- helpers available to subclasses ------------------------------------

    def execute_sql(
        self,
        db: Session,
        query_name: str,
        params: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        sql = self.queries.get(query_name)
        if sql is None:
            raise KeyError(
                f"Dataset '{self.id}' has no query named '{query_name}'. "
                f"Available: {sorted(self.queries)}"
            )
        result = db.execute(text(sql), params or {})
        return pd.DataFrame(result.mappings().all())

    def describe(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "filters": self.config.get("filters", []),
            "queries": sorted(self.queries),
            "config": self.config,
        }

    # ---- subclass contract --------------------------------------------------

    @abstractmethod
    def run(self, db: Session, filters: dict[str, Any]) -> DatasetResult:
        """Execute the dataset and return a `DatasetResult`."""
