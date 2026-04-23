"""TSMA Postgres loader for the spend tracking workbook."""

from __future__ import annotations

import os
import re
from collections import defaultdict

try:
    import psycopg
except ImportError:  # pragma: no cover - optional at import time
    psycopg = None

from sheet_utils import FIRST_MONTH, MONTH_COLS

YEARS = (2024, 2025, 2026)
MONTH_CODES = [f"{year}{month:02d}" for year in YEARS for month in range(1, 13)]
MONTH_INDEX = {code: idx for idx, code in enumerate(MONTH_CODES)}

ENTITY_ALIASES = {
    "GOBC": "Gov BC",
    "GOVBC": "Gov BC",
    "GOVERNMENTOFBRITISHCOLUMBIA": "Gov BC",
    "BCLC": "BCLC",
    "BCHYDRO": "BC Hydro",
    "BCHYDROPOWERAUTHORITY": "BC Hydro",
    "WSBC": "WSBC",
    "WORKSAFEBC": "WSBC",
    "WORKSAFEBRITISHCOLUMBIA": "WSBC",
    "ECC": "ECC",
    "TMOE": "ECC",
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
    "SCHOOLDISTRICTS": "School Districts",
}

DATA_TOWERS = ("Business Internet", "Data - WAN")
VOICE_TOWERS = ("Conferencing", "Long Distance", "Voice")
OUT_OF_SCOPE_TOWERS = ("Managed WLAN",)
OTHER_OUT_OF_SCOPE_TOWERS = ("Managed Router", "Managed Security", "INM")
LITE_CONFERENCING_TOWERS = ("Conferencing",)
LITE_LONG_DISTANCE_TOWERS = ("Long Distance",)
LITE_VOICE_TOWERS = ("Voice",)


def _blank_amounts() -> list[float]:
    return [0.0 for _ in MONTH_CODES]


def _normalize_entity_key(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", value.upper())


def canonical_entity_name(value: object) -> str:
    name = str(value).strip()
    if not name:
        return ""
    return ENTITY_ALIASES.get(_normalize_entity_key(name), name)


def _load_amount_map(conn, sql: str, params: tuple, entity_idx: int = 0) -> dict[str, list[float]]:
    results: dict[str, list[float]] = defaultdict(_blank_amounts)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        for row in cur.fetchall():
            entity = canonical_entity_name(row[entity_idx])
            month_code = str(row[entity_idx + 1])
            amount = float(row[entity_idx + 2] or 0)
            month_idx = MONTH_INDEX.get(month_code)
            if not entity or month_idx is None:
                continue
            results[entity][month_idx] += amount
    return dict(results)


def load_cellular(conn) -> dict[str, list[float]]:
    return _load_amount_map(
        conn,
        """
        SELECT lcd_category, ccyymm, COALESCE(SUM(billed_amt), 0)
        FROM public.tsma_wireless
        WHERE ccyymm BETWEEN %s AND %s
          AND NULLIF(TRIM(COALESCE(lcd_category, '')), '') IS NOT NULL
        GROUP BY lcd_category, ccyymm
        ORDER BY lcd_category, ccyymm
        """,
        (MONTH_CODES[0], MONTH_CODES[-1]),
    )


def load_wireline(conn, service_towers: tuple[str, ...]) -> dict[str, list[float]]:
    return _load_amount_map(
        conn,
        """
        SELECT entity, ccyymm, COALESCE(SUM(billed_amt), 0)
        FROM public.tsma_wireline
        WHERE ccyymm BETWEEN %s AND %s
          AND tsma_service_tower = ANY(%s)
          AND NULLIF(TRIM(COALESCE(entity, '')), '') IS NOT NULL
        GROUP BY entity, ccyymm
        ORDER BY entity, ccyymm
        """,
        (MONTH_CODES[0], MONTH_CODES[-1], list(service_towers)),
    )


def load_other_out_of_scope(conn) -> dict[str, list[float]]:
    return _load_amount_map(
        conn,
        """
        SELECT entity, ccyymm, COALESCE(SUM(billed_amt), 0)
        FROM public.tsma_other
        WHERE ccyymm BETWEEN %s AND %s
          AND tsma_service_tower = ANY(%s)
          AND NULLIF(TRIM(COALESCE(entity, '')), '') IS NOT NULL
        GROUP BY entity, ccyymm
        ORDER BY entity, ccyymm
        """,
        (MONTH_CODES[0], MONTH_CODES[-1], list(OTHER_OUT_OF_SCOPE_TOWERS)),
    )


def load_lite_cellular(conn) -> dict[str, list[float]]:
    results: dict[str, list[float]] = defaultdict(_blank_amounts)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ccyymm, COALESCE(SUM(billed_amt), 0)
            FROM public.tsma_lite_wireless
            WHERE ccyymm BETWEEN %s AND %s
            GROUP BY ccyymm
            ORDER BY ccyymm
            """,
            (MONTH_CODES[0], MONTH_CODES[-1]),
        )
        for month_code, amount in cur.fetchall():
            month_idx = MONTH_INDEX.get(str(month_code))
            if month_idx is not None:
                results["School Districts"][month_idx] += float(amount or 0)
    return dict(results)


def load_lite_wireline(conn, service_towers: tuple[str, ...]) -> dict[str, list[float]]:
    results: dict[str, list[float]] = defaultdict(_blank_amounts)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ccyymm, COALESCE(SUM(billed_amt), 0)
            FROM public.tsma_lite_wireline
            WHERE ccyymm BETWEEN %s AND %s
              AND tsma_service_tower = ANY(%s)
            GROUP BY ccyymm
            ORDER BY ccyymm
            """,
            (MONTH_CODES[0], MONTH_CODES[-1], list(service_towers)),
        )
        for month_code, amount in cur.fetchall():
            month_idx = MONTH_INDEX.get(str(month_code))
            if month_idx is not None:
                results["School Districts"][month_idx] += float(amount or 0)
    return dict(results)


def load_ivr_totals(conn) -> list[float]:
    totals = _blank_amounts()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ccyymm, COALESCE(SUM(billed_amt), 0)
            FROM public.tsma_ivr
            WHERE ccyymm BETWEEN %s AND %s
            GROUP BY ccyymm
            ORDER BY ccyymm
            """,
            (MONTH_CODES[0], MONTH_CODES[-1]),
        )
        for month_code, amount in cur.fetchall():
            month_idx = MONTH_INDEX.get(str(month_code))
            if month_idx is not None:
                totals[month_idx] += float(amount or 0)
    return totals


def load_mms(conn) -> dict[str, list[float]]:
    return _load_amount_map(
        conn,
        """
        SELECT entity_name, ccyymm, COALESCE(SUM(total), 0)
        FROM public.tsma_mms
        WHERE ccyymm BETWEEN %s AND %s
          AND NULLIF(TRIM(COALESCE(entity_name, '')), '') IS NOT NULL
        GROUP BY entity_name, ccyymm
        ORDER BY entity_name, ccyymm
        """,
        (MONTH_CODES[0], MONTH_CODES[-1]),
    )


def merge_maps(*maps: dict[str, list[float]]) -> dict[str, list[float]]:
    merged: dict[str, list[float]] = defaultdict(_blank_amounts)
    for data in maps:
        for entity, amounts in data.items():
            for idx, amount in enumerate(amounts):
                merged[entity][idx] += amount
    return dict(merged)


def load_tsma_lite_data(dsn: str | None = None) -> dict[tuple[str, int], float]:
    """Return {(row_type, excel_col): value} for TSMA Lite monthly rows."""
    dsn = dsn or os.environ.get("DATABASE_URL")
    if not dsn or psycopg is None:
        return {}

    with psycopg.connect(dsn) as conn:
        conferencing = load_lite_wireline(conn, LITE_CONFERENCING_TOWERS).get("School Districts", _blank_amounts())
        long_distance = load_lite_wireline(conn, LITE_LONG_DISTANCE_TOWERS).get("School Districts", _blank_amounts())
        voice = load_lite_wireline(conn, LITE_VOICE_TOWERS).get("School Districts", _blank_amounts())
        cellular = load_lite_cellular(conn).get("School Districts", _blank_amounts())

    data: dict[tuple[str, int], float] = {}
    for row_type, amounts in (
        ("conferencing", conferencing),
        ("long_distance", long_distance),
        ("voice", voice),
        ("cellular", cellular),
    ):
        for month_idx, amount in enumerate(amounts):
            if amount:
                data[(row_type, FIRST_MONTH + month_idx)] = amount

    return data


def load_tsma_data(dsn: str | None = None) -> dict[tuple[str, str, int], float]:
    """Return {(bge_name, row_type, excel_col): value} for TSMA section detail rows."""
    dsn = dsn or os.environ.get("DATABASE_URL")
    if not dsn or psycopg is None:
        return {}

    with psycopg.connect(dsn) as conn:
        cellular_map = merge_maps(load_cellular(conn), load_lite_cellular(conn))
        data_map = merge_maps(load_wireline(conn, DATA_TOWERS), load_lite_wireline(conn, DATA_TOWERS))
        voice_map = merge_maps(load_wireline(conn, VOICE_TOWERS), load_lite_wireline(conn, VOICE_TOWERS))
        mms_map = load_mms(conn)
        oos_map = merge_maps(
            load_wireline(conn, OUT_OF_SCOPE_TOWERS),
            load_lite_wireline(conn, OUT_OF_SCOPE_TOWERS),
            load_other_out_of_scope(conn),
        )
        ivr_totals = load_ivr_totals(conn)

    data: dict[tuple[str, str, int], float] = {}

    def add_amounts(entity: str, row_type: str, amounts: list[float]) -> None:
        for month_idx, amount in enumerate(amounts):
            if amount:
                data[(entity, row_type, FIRST_MONTH + month_idx)] = amount

    for entity, amounts in cellular_map.items():
        add_amounts(entity, "cellular", amounts)
    for entity, amounts in data_map.items():
        add_amounts(entity, "data", amounts)
    for entity, amounts in voice_map.items():
        add_amounts(entity, "voice", amounts)
    for entity, amounts in mms_map.items():
        add_amounts(entity, "mms", amounts)
    for entity, amounts in oos_map.items():
        add_amounts(entity, "oos", amounts)
    add_amounts("Gov BC", "voice_ivr", ivr_totals)

    return data


def write_tsma_detail_row(ws, row_num: int, col_fmt, tsma_data: dict, bge_name: str, row_type: str) -> None:
    for col in MONTH_COLS:
        amount = tsma_data.get((bge_name, row_type, col), 0)
        ws.write_number(row_num - 1, col, round(amount, 2), col_fmt)
