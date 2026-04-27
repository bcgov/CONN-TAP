"""TSMA section CSV loader for the spend tracking workbook.

Reads TSMA monthly spend from component CSVs in scripts/source and returns the
same data shapes as tsma.py, without opening a database connection.

Main TSMA component CSVs:
  tsma_cellular_spend.csv      -> row type cellular
  tsma_mms_spend.csv           -> row type mms
  tsma_data_spend.csv          -> row type data
  tsma_voice_spend.csv         -> row type voice
  tsma_voice_ivr_spend.csv     -> row type voice_ivr

Expected main TSMA CSV columns:
  entity_key, month_start, amount

TSMA Out of Scope is reused from tsma_other_spend.csv.

TSMA Lite CSV:
  tsma_lite_spend.csv

Expected TSMA Lite CSV columns:
  month_start, conferencing_spend, long_distance_spend, voice_spend, cellular_spend
"""

from __future__ import annotations

import csv
import os
import re
from datetime import datetime

from sheet_utils import FIRST_MONTH, LAST_MONTH, MONTH_COLS
from tsma_other import load_tsma_other

SOURCE_DIR = os.path.join(os.path.dirname(__file__), "source")

ENTITY_KEY_MAP = {
    "BCH": "BC Hydro",
    "BCLC": "BCLC",
    "BC HYDRO": "BC Hydro",
    "BC HYDRO POWER AUTHORITY": "BC Hydro",
    "BC HYDRO & POWER AUTHORITY": "BC Hydro",
    "ECC": "ECC",
    "MOE": "ECC",
    "TMOE": "ECC",
    "MINISTRY OF EDUCATION": "ECC",
    "MINISTRY OF EDUCATION AND CHILD CARE": "ECC",
    "FHA": "FHA",
    "FRASER HEALTH": "FHA",
    "FRASER HEALTH AUTHORITY": "FHA",
    "FNHA": "FNHA",
    "FIRST NATIONS HEALTH AUTHORITY": "FNHA",
    "GBC": "Gov BC",
    "GOBC": "Gov BC",
    "GOVBC": "Gov BC",
    "GOV BC": "Gov BC",
    "GOVERNMENT OF BC": "Gov BC",
    "GOVERNMENT OF BRITISH COLUMBIA": "Gov BC",
    "ICBC": "ICBC",
    "INSURANCE CORPORATION OF BRITISH COLUMBIA": "ICBC",
    "IHA": "IHA",
    "INTERIOR HEALTH": "IHA",
    "INTERIOR HEALTH AUTHORITY": "IHA",
    "NHA": "NHA",
    "NORTHERN HEALTH": "NHA",
    "NORTHERN HEALTH AUTHORITY": "NHA",
    "PHC": "VCHA",
    "PHSA": "PHSA",
    "PROVINCIAL HEALTH SERVICES": "PHSA",
    "PROVINCIAL HEALTH SERVICES AUTHORITY": "PHSA",
    "SD": "School Districts",
    "SCHOOL DISTRICT": "School Districts",
    "SCHOOL DISTRICTS": "School Districts",
    "VCHA": "VCHA",
    "VCHA PHC": "VCHA",
    "VANCOUVER COASTAL HEALTH": "VCHA",
    "VANCOUVER COASTAL HEALTH AUTHORITY": "VCHA",
    "VANCOUVER ISLAND HEALTH": "VIHA",
    "VANCOUVER ISLAND HEALTH AUTHORITY": "VIHA",
    "VIHA": "VIHA",
    "WORKERS COMPENSATION BOARD": "WSBC",
    "WORKERS COMPENSATION BOARD OF BRITISH COLUMBIA": "WSBC",
    "WORKSAFEBC": "WSBC",
    "WSBC": "WSBC",
}
ENTITY_LOOKUP = {
    alias: bge
    for key, bge in ENTITY_KEY_MAP.items()
    for alias in (key, re.sub(r"[^A-Z0-9]+", "", key))
}

TSMA_OTHER_ORG_MAP = {
    "BRITISH COLUMBIA HYDRO & POWER AUTHORITY": "BC Hydro",
    "BRITISH COLUMBIA LIQUOR DISTRIBUTION BRANCH": "Gov BC",
    "CHILDRENS & WOMENS HEALTH CENTRE OF BC SOCIETY": "PHSA",
    "FIRST NATIONS HEALTH AUTHORITY": "FNHA",
    "FRASER HEALTH AUTHORITY": "FHA",
    "GBC - LIQUOR DISTRIBUTION BRANCH": "Gov BC",
    "GBC - MINISTRY OF CITIZENS SERVICES": "Gov BC",
    "GBC - MINISTRY OF EDUCATION & CHILD CARE": "ECC",
    "GBC - MINISTRY OF HEALTH": "Gov BC",
    "GBC - OFFICE OF THE CHIEF INFORMATION OFFICER": "Gov BC",
    "GBC - SHARED SERVICES BC": "Gov BC",
    "GREATER VANCOUVER MENTAL HEALTH SERVICE": "VCHA",
    "INSURANCE CORPORATION OF BRITISH COLUMBIA - ICBC": "ICBC",
    "PROVINCIAL HEALTH SERVICES AUTHORITY": "PHSA",
    "VANCOUVER COASTAL HEALTH AUTHORITY": "VCHA",
    "VANCOUVER COASTAL HEALTH AUTHORITY HOWE SOUND HOME SUPPORT SERVICES": "VCHA",
    "VANCOUVER COASTAL HEALTH AUTHORITY O/A LIONS GATE HOSPITAL": "VCHA",
    "VANCOUVER COASTAL HEALTH AUTHORITY O/A OLIVE DEVAUD RESIDENCE": "VCHA",
    "WORKERS COMPENSATION BOARD OF BRITISH COLUMBIA": "WSBC",
}

TSMA_COMPONENT_CSVS = {
    "cellular": "tsma_cellular_spend.csv",
    "mms": "tsma_mms_spend.csv",
    "data": "tsma_data_spend.csv",
    "voice": "tsma_voice_spend.csv",
    "voice_ivr": "tsma_voice_ivr_spend.csv",
}

TSMA_LITE_CSV = "tsma_lite_spend.csv"

TSMA_LITE_COL_MAP = {
    "conferencing_spend": "conferencing",
    "long_distance_spend": "long_distance",
    "voice_spend": "voice",
    "cellular_spend": "cellular",
}


def _normalize_key(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).replace("\u00a0", " ").strip()).upper()


def _entity_key(value: object) -> str:
    raw = _normalize_key(value)
    compact = re.sub(r"[^A-Z0-9]+", "", raw)
    return ENTITY_LOOKUP.get(raw) or ENTITY_LOOKUP.get(compact, "")


def _month_to_col(month_str: str):
    """Parse a month_start string -> 0-based Excel column, or None if out of range."""
    s = month_str.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y/%m/%d", "%Y/%m", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(s, fmt)
            col = FIRST_MONTH + (dt.year - 2024) * 12 + (dt.month - 1)
            return col if FIRST_MONTH <= col <= LAST_MONTH else None
        except ValueError:
            continue
    return None


def _amount(value: str) -> float | None:
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _read_rows(path: str):
    if not os.path.exists(path):
        return

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        reader.fieldnames = [h.strip().lower() for h in (reader.fieldnames or [])]
        yield from reader


def _component_path(source_dir: str, filename: str) -> str:
    return os.path.join(source_dir, filename)


def load_tsma_data(source_dir: str = SOURCE_DIR) -> dict[tuple[str, str, int], float]:
    """Read TSMA component CSVs and return {(bge_name, row_type, col_idx): value}."""
    data: dict[tuple[str, str, int], float] = {}
    for row_type, filename in TSMA_COMPONENT_CSVS.items():
        for row in _read_rows(_component_path(source_dir, filename)) or ():
            bge = _entity_key(row.get("entity_key", ""))
            if not bge:
                continue
            col = _month_to_col(row.get("month_start", ""))
            if col is None:
                continue
            val = _amount(row.get("amount", ""))
            if val is None:
                continue
            key = (bge, row_type, col)
            data[key] = data.get(key, 0.0) + val

    for (_feed, org, col), amount in load_tsma_other(_component_path(source_dir, "tsma_other_spend.csv")).items():
        bge = TSMA_OTHER_ORG_MAP.get(org)
        if not bge:
            continue
        key = (bge, "oos", col)
        data[key] = data.get(key, 0.0) + amount

    for (lite_type, col), amount in load_tsma_lite_data(source_dir).items():
        if lite_type == "cellular":
            row_type = "cellular"
        elif lite_type in ("conferencing", "long_distance", "voice"):
            row_type = "voice"
        else:
            continue
        key = ("School Districts", row_type, col)
        data[key] = data.get(key, 0.0) + amount

    return data


def load_tsma_lite_data(source_dir: str = SOURCE_DIR) -> dict[tuple[str, int], float]:
    """Read tsma_lite_spend.csv and return {(row_type, col_idx): value}."""
    data: dict[tuple[str, int], float] = {}
    for row in _read_rows(_component_path(source_dir, TSMA_LITE_CSV)) or ():
        col = _month_to_col(row.get("month_start", ""))
        if col is None:
            continue
        for csv_col, row_type in TSMA_LITE_COL_MAP.items():
            val = _amount(row.get(csv_col, ""))
            if val is None:
                continue
            key = (row_type, col)
            data[key] = data.get(key, 0.0) + val

    return data


def write_tsma_detail_row(ws, row_num: int, col_fmt, tsma_data: dict, bge_name: str, row_type: str) -> None:
    for col in MONTH_COLS:
        amount = tsma_data.get((bge_name, row_type, col), 0)
        ws.write_number(row_num - 1, col, round(amount, 2), col_fmt)
