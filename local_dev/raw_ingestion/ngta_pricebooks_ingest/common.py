"""Shared helpers for NGTA pricebook folder ingestion."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal, Optional

import pandas as pd

PG_SCHEMA = "raw_data"
Provider = Literal["telus", "rogers"]


def fq(ident: str) -> str:
    return f"{PG_SCHEMA}.{ident}"


def parse_period(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    ts = pd.to_datetime(s, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Invalid --source-period: {s!r}")
    d = ts.date()
    return date(d.year, d.month, 1)


def provider_from_path(path: Path, root: Path, force: Optional[Provider]) -> Optional[Provider]:
    if force:
        return force
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    for part in rel.parts[:-1]:
        low = part.casefold()
        if low == "telus":
            return "telus"
        if low == "rogers":
            return "rogers"
    return None


def iter_pricebook_files(folder: Path, recursive: bool) -> list[Path]:
    patterns = ("*.pdf", "*.xlsx", "*.xlsm")
    paths: list[Path] = []
    if recursive:
        for pat in patterns:
            paths.extend(folder.rglob(pat))
    else:
        for pat in patterns:
            paths.extend(folder.glob(pat))
        for sub in ("rogers", "telus"):
            subdir = folder / sub
            if subdir.is_dir():
                for pat in patterns:
                    paths.extend(subdir.glob(pat))
    return sorted(p for p in paths if not p.name.startswith("~$") and not p.name.startswith("."))


def iter_pricebook_pdfs(folder: Path, recursive: bool) -> list[Path]:
    """Deprecated alias; use iter_pricebook_files."""
    return [p for p in iter_pricebook_files(folder, recursive) if p.suffix.lower() == ".pdf"]
