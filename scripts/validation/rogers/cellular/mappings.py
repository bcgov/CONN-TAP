# mappings.py
#
# BGE_MAP and SUB_BGE_TO_BGE are loaded from the dbt seed CSVs and reference
# SQL so this script stays in sync with the rest of the platform automatically.

import csv
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).parents[4]
_SEEDS_DIR = _REPO_ROOT / "app" / "backend" / "dbt" / "seeds"
_REF_DIR   = _REPO_ROOT / "app" / "backend" / "alembic" / "reference_data"


def _load_bge_map() -> dict:
    """raw BGE name → BGE code, from bge_alias_map.csv"""
    path = _SEEDS_DIR / "bge_alias_map.csv"
    with open(path, newline="", encoding="utf-8") as f:
        return {row["raw_name"]: row["bge_alias"] for row in csv.DictReader(f)}


def _load_sub_bge_to_bge() -> dict:
    """raw SUB-BGE name → BGE code, built from sub_bge_alias_map.csv + sub_bge.sql"""

    # Step 1: raw sub-BGE name → canonical sub-BGE code
    alias_path = _SEEDS_DIR / "sub_bge_alias_map.csv"
    with open(alias_path, newline="", encoding="utf-8") as f:
        raw_to_canonical = {
            row["raw_name"]: row["sub_bge_alias"] for row in csv.DictReader(f)
        }

    # Step 2: canonical sub-BGE code → BGE code (parsed from sub_bge.sql INSERTs)
    sql_text = (_REF_DIR / "sub_bge.sql").read_text(encoding="utf-8")
    pattern = re.compile(
        r"\('([^']+)',\s*'[^']*',\s*\(SELECT id FROM reference_data\.bge WHERE code = '([^']+)'\)"
    )
    canonical_to_bge = {m.group(1): m.group(2) for m in pattern.finditer(sql_text)}

    # Step 3: combine
    return {
        raw: canonical_to_bge[canonical]
        for raw, canonical in raw_to_canonical.items()
        if canonical in canonical_to_bge
    }


BGE_MAP        = _load_bge_map()
SUB_BGE_TO_BGE = _load_sub_bge_to_bge()
