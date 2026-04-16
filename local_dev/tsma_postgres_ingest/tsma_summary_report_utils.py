from __future__ import annotations

import calendar
import re
from collections import defaultdict
from decimal import Decimal

import psycopg

YEARS = (2024, 2025, 2026)
MONTH_CODES = [f"{year}{month:02d}" for year in YEARS for month in range(1, 13)]
MONTH_HEADERS = [f"{calendar.month_abbr[month]} {year}" for year in YEARS for month in range(1, 13)]
ENTITY_ORDER = [
    "GoBC",
    "BCLC",
    "BC HYDRO",
    "WorkSafe BC",
    "TMOE",
    "FHA",
    "NHA",
    "ICBC",
    "PHSA",
    "IHA",
    "VIHA",
    "FNHA",
    "VCHA",
    "School Districts",
]
ENTITY_ALIASES = {
    "GOBC": "GoBC",
    "GOVBC": "GoBC",
    "GOVERNMENTOFBRITISHCOLUMBIA": "GoBC",
    "BCLC": "BCLC",
    "BCHYDRO": "BC HYDRO",
    "BCHYDROPOWERAUTHORITY": "BC HYDRO",
    "WSBC": "WorkSafe BC",
    "WORKSAFEBC": "WorkSafe BC",
    "WORKSAFEBRITISHCOLUMBIA": "WorkSafe BC",
    "ECC": "TMOE",
    "TMOE": "TMOE",
    "FHA": "FHA",
    "NHA": "NHA",
    "ICBC": "ICBC",
    "PHSA": "PHSA",
    "IHA": "IHA",
    "VIHA": "VIHA",
    "FNHA": "FNHA",
    "VCHA": "VCHA",
    "PHC": "VCHA",
    "VCHAPHC": "VCHA",
    "VANCOUVERCOASTALHEALTHAUTHORITYPROVIDENCEHEALTHCARE": "VCHA",
}
DATA_TOWERS = ("Business Internet", "Data - WAN")
VOICE_TOWERS = ("Conferencing", "Long Distance", "Voice")
OUT_OF_SCOPE_TOWERS = ("Managed WLAN",)


def blank_amounts() -> list[Decimal]:
    return [Decimal("0") for _ in MONTH_CODES]


def normalize_entity_key(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", value.upper())


def canonical_entity_name(value: object) -> str:
    name = str(value).strip()
    if not name:
        return ""
    return ENTITY_ALIASES.get(normalize_entity_key(name), name)


def load_cellular(conn: psycopg.Connection) -> dict[str, list[Decimal]]:
    results: dict[str, list[Decimal]] = defaultdict(blank_amounts)
    sql = """
        SELECT lcd_category, ccyymm, COALESCE(SUM(billed_amt), 0)
        FROM public.tsma_wireless
        WHERE ccyymm BETWEEN %s AND %s
          AND NULLIF(TRIM(COALESCE(lcd_category, '')), '') IS NOT NULL
        GROUP BY lcd_category, ccyymm
        ORDER BY lcd_category, ccyymm
    """
    with conn.cursor() as cur:
        cur.execute(sql, (MONTH_CODES[0], MONTH_CODES[-1]))
        for entity, ccyymm, amount in cur.fetchall():
            idx = MONTH_CODES.index(str(ccyymm))
            canonical_name = canonical_entity_name(entity)
            if not canonical_name:
                continue
            results[canonical_name][idx] += amount or Decimal("0")
    return dict(results)


def load_lite_cellular(conn: psycopg.Connection) -> dict[str, list[Decimal]]:
    results: dict[str, list[Decimal]] = defaultdict(blank_amounts)
    sql = """
        SELECT ccyymm, COALESCE(SUM(billed_amt), 0)
        FROM public.tsma_lite_wireless
        WHERE ccyymm BETWEEN %s AND %s
        GROUP BY ccyymm
        ORDER BY ccyymm
    """
    with conn.cursor() as cur:
        cur.execute(sql, (MONTH_CODES[0], MONTH_CODES[-1]))
        for ccyymm, amount in cur.fetchall():
            idx = MONTH_CODES.index(str(ccyymm))
            results["School Districts"][idx] += amount or Decimal("0")
    return dict(results)


def load_wireline(conn: psycopg.Connection, service_towers: tuple[str, ...]) -> dict[str, list[Decimal]]:
    results: dict[str, list[Decimal]] = defaultdict(blank_amounts)
    sql = """
        SELECT entity, ccyymm, COALESCE(SUM(billed_amt), 0)
        FROM public.tsma_wireline
        WHERE ccyymm BETWEEN %s AND %s
          AND tsma_service_tower = ANY(%s)
          AND NULLIF(TRIM(COALESCE(entity, '')), '') IS NOT NULL
        GROUP BY entity, ccyymm
        ORDER BY entity, ccyymm
    """
    with conn.cursor() as cur:
        cur.execute(sql, (MONTH_CODES[0], MONTH_CODES[-1], list(service_towers)))
        for entity, ccyymm, amount in cur.fetchall():
            idx = MONTH_CODES.index(str(ccyymm))
            canonical_name = canonical_entity_name(entity)
            if not canonical_name:
                continue
            results[canonical_name][idx] += amount or Decimal("0")
    return dict(results)


def load_lite_wireline(conn: psycopg.Connection, service_towers: tuple[str, ...]) -> dict[str, list[Decimal]]:
    results: dict[str, list[Decimal]] = defaultdict(blank_amounts)
    sql = """
        SELECT ccyymm, COALESCE(SUM(billed_amt), 0)
        FROM public.tsma_lite_wireline
        WHERE ccyymm BETWEEN %s AND %s
          AND tsma_service_tower = ANY(%s)
        GROUP BY ccyymm
        ORDER BY ccyymm
    """
    with conn.cursor() as cur:
        cur.execute(sql, (MONTH_CODES[0], MONTH_CODES[-1], list(service_towers)))
        for ccyymm, amount in cur.fetchall():
            idx = MONTH_CODES.index(str(ccyymm))
            results["School Districts"][idx] += amount or Decimal("0")
    return dict(results)


def load_ivr_totals(conn: psycopg.Connection) -> list[Decimal]:
    totals = blank_amounts()
    sql = """
        SELECT ccyymm, COALESCE(SUM(billed_amt), 0)
        FROM public.tsma_ivr
        WHERE ccyymm BETWEEN %s AND %s
        GROUP BY ccyymm
        ORDER BY ccyymm
    """
    with conn.cursor() as cur:
        cur.execute(sql, (MONTH_CODES[0], MONTH_CODES[-1]))
        for ccyymm, amount in cur.fetchall():
            idx = MONTH_CODES.index(str(ccyymm))
            totals[idx] += amount or Decimal("0")
    return totals


def sum_maps(data: dict[str, list[Decimal]]) -> list[Decimal]:
    totals = blank_amounts()
    for amounts in data.values():
        for i, amount in enumerate(amounts):
            totals[i] += amount
    return totals


def merge_maps(*maps: dict[str, list[Decimal]]) -> dict[str, list[Decimal]]:
    merged: dict[str, list[Decimal]] = defaultdict(blank_amounts)
    for data in maps:
        for entity, amounts in data.items():
            for idx, amount in enumerate(amounts):
                merged[entity][idx] += amount
    return dict(merged)


def entity_names(*maps: dict[str, list[Decimal]]) -> list[str]:
    names: set[str] = set()
    for data in maps:
        names.update(data.keys())
    ordered = [name for name in ENTITY_ORDER if name in names]
    remaining = sorted(name for name in names if name not in ENTITY_ORDER)
    return ordered + remaining
