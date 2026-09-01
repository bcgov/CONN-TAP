"""Query and table-building helpers for the spend summary dataset.

The table is seeded from the full predefined reference_data hierarchy (every BGE /
sub_bge / service_designee), then the finest-grain (bge, sub_bge, service_category)
spend rows are overlaid — so entities with no data still appear as zero rows rather
than dropping out. BGE rows roll up all their descendants, Sub-org rows roll up
their Service Designee children, and each service category becomes a column.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd

from app.datasets.base import DatasetResult
from app.datasets.chart_format import to_float
from app.datasets.spend_common import Filters

# Fixed column order (code -> display name), matching the summary table mockup.
CATEGORY_ORDER: tuple[tuple[str, str], ...] = (
    ("voice", "Voice"),
    ("data", "Data"),
    ("cellular", "Cellular"),
    ("professional_services", "Professional Services"),
    ("time_limited_services", "Time Limited Services"),
    # Spend we can't attribute to a real service (eg. Rogers rows with no
    # productline: late fees, credit memos). Always last.
    ("unknown", "Unknown"),
)
CATEGORY_CODES: tuple[str, ...] = tuple(code for code, _ in CATEGORY_ORDER)

_TYPE_LABEL = {"sub_org": "Sub Org", "service_designee": "Service Designee"}

# The BGE-direct "extra" is split into one line per source family. Order here is
# the display order when both are present.
_SOURCE_LABEL: tuple[tuple[str, str], ...] = (("ngta", "NGTA"), ("tsma", "TSMA"))

RESULT_COLUMNS = ["entity_name", "entity_type", "level", *CATEGORY_CODES, "total_millions"]


def _empty_values() -> dict[str, float]:
    return dict.fromkeys(CATEGORY_CODES, 0.0)


def _total(values: dict[str, float]) -> float:
    return sum(values.get(code, 0.0) for code in CATEGORY_CODES)


def _row(
    node_id: str,
    parent_id: str | None,
    name: str,
    entity_type: str,
    level: int,
    values: dict[str, float],
) -> dict[str, Any]:
    ordered = {code: round(values.get(code, 0.0), 6) for code in CATEGORY_CODES}
    return {
        "id": node_id,
        "parent_id": parent_id,
        "name": name,
        "type": entity_type,
        "level": level,
        "values": ordered,
        "total": round(_total(values), 6),
    }


def _scaffold(scaffold_df: pd.DataFrame) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
    """Seed the per-BGE and per-sub_bge structures from the full predefined
    reference_data hierarchy, every entity starting at zero spend.

    Returns (bges, subs) in the same shape `_aggregate` overlays spend onto, so
    entities with no data still surface as zero rows.
    """
    bges: dict[int, dict[str, Any]] = {}
    subs: dict[int, dict[str, Any]] = {}

    for r in scaffold_df.itertuples(index=False):
        bge_id = int(r.bge_id)
        bges.setdefault(
            bge_id, {"code": str(r.bge_code), "name": str(r.bge_name), "values": _empty_values()}
        )
        if pd.notna(r.sub_bge_id):
            sub_id = int(r.sub_bge_id)
            parent = int(r.parent_sub_bge_id) if pd.notna(r.parent_sub_bge_id) else None
            subs.setdefault(
                sub_id,
                {
                    "name": str(r.sub_bge_name),
                    "entity_type": str(r.entity_type),
                    "parent_sub_bge_id": parent,
                    "bge_id": bge_id,
                    "values": _empty_values(),
                },
            )

    return bges, subs


def _aggregate(
    df: pd.DataFrame,
    bges: dict[int, dict[str, Any]],
    subs: dict[int, dict[str, Any]],
    direct: dict[int, dict[str, dict[str, float]]],
) -> None:
    """Overlay the finest-grain spend rows onto the pre-seeded scaffold, folding
    them into per-BGE and per-sub_bge running totals in place.

      bges:   bge_id -> {code, name, values(total of everything under it)}
      subs:   sub_bge_id -> {name, entity_type, parent_sub_bge_id, bge_id, values(own spend)}
      direct: bge_id -> source_group -> values(BGE-direct spend, sub_bge_id null),
              the source split of the "extra" the summary shows as a "BGE" line.

    Rows always resolve against a seeded entity (FKs into reference_data); the
    `setdefault` fallbacks only guard against a scaffold/spend mismatch.
    """
    for r in df.itertuples(index=False):
        bge_id = int(r.bge_id)
        # Cellular Hardware displays as part of Cellular in UI.
        cat = str(r.service_category_code)
        if cat == "cellular_hardware":
            cat = "cellular"
        millions = to_float(r.spend_millions)

        bge = bges.setdefault(
            bge_id, {"code": str(r.bge_code), "name": str(r.bge_name), "values": _empty_values()}
        )
        bge["values"][cat] = bge["values"].get(cat, 0.0) + millions

        if pd.notna(r.sub_bge_id):
            sub_id = int(r.sub_bge_id)
            parent = int(r.parent_sub_bge_id) if pd.notna(r.parent_sub_bge_id) else None
            sub = subs.setdefault(
                sub_id,
                {
                    "name": str(r.sub_bge_name),
                    "entity_type": str(r.entity_type),
                    "parent_sub_bge_id": parent,
                    "bge_id": bge_id,
                    "values": _empty_values(),
                },
            )
            sub["values"][cat] = sub["values"].get(cat, 0.0) + millions
        else:
            # BGE-direct spend (no sub_bge): record it by source family so the
            # residue line can be split into TSMA vs NGTA.
            src = str(r.source_group)
            by_source = direct.setdefault(bge_id, {})
            values = by_source.setdefault(src, _empty_values())
            values[cat] = values.get(cat, 0.0) + millions


def _display_values(
    subs: dict[int, dict[str, Any]],
    children_by_parent: dict[int, list[int]],
    sub_id: int,
) -> dict[str, float]:
    """Sub-org display = own spend + its Service Designee children; SD = own."""
    values = dict(subs[sub_id]["values"])
    for child_id in children_by_parent.get(sub_id, ()):
        for code, amt in subs[child_id]["values"].items():
            values[code] = values.get(code, 0.0) + amt
    return values


def _residue_rows(
    bge_node_id: str,
    bge: dict[str, Any],
    direct_by_source: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    """The BGE's own spend (no sub_bge), split into one "BGE" line per source
    family (NGTA / TSMA) so the nested rows reconcile to the total. Emits a line
    only for a source whose direct spend is non-zero; empty list when none.

    The sum across sources equals the old single residue (BGE total minus
    everything attributed to sub_orgs / service designees), since every non-direct
    row lands under a sub_bge and every direct row is bucketed here by source.
    """
    rows: list[dict[str, Any]] = []
    for src, label in _SOURCE_LABEL:
        values = direct_by_source.get(src)
        if values is None or round(_total(values), 6) <= 0:
            continue
        rows.append(
            _row(
                f"{bge_node_id}:direct:{src}",
                bge_node_id,
                f"{bge['name']} ({label})",
                "BGE",
                1,
                values,
            )
        )
    return rows


def _emit_level1_rows(
    bge_node_id: str,
    sub_id: int,
    subs: dict[int, dict[str, Any]],
    children_by_parent: dict[int, list[int]],
) -> list[dict[str, Any]]:
    """One level-1 node (Sub-org or parentless Service Designee): its roll-up /
    leaf row, then — for a sub-org with children — a "Sub Org" line for its own
    spend not booked under a designee, followed by its Service Designee children.
    The own-spend line leads the children so the direct row sits first."""
    sub = subs[sub_id]
    sub_node_id = f"sub:{sub_id}"
    rows: list[dict[str, Any]] = []

    children = (
        sorted(
            children_by_parent.get(sub_id, ()),
            key=lambda c: (-_total(subs[c]["values"]), subs[c]["name"]),
        )
        if sub["entity_type"] == "sub_org"
        else []
    )

    label = _TYPE_LABEL.get(sub["entity_type"], sub["entity_type"])
    values = _display_values(subs, children_by_parent, sub_id)
    rows.append(_row(sub_node_id, bge_node_id, sub["name"], label, 1, values))

    # The designee children roll up leaf values, so the sub-org's own spend is
    # exactly what's left of its total — shown as a "Sub Org" line when non-zero,
    # placed first among the sub-org's nested rows.
    if children:
        own = sub["values"]
        if round(_total(own), 6) > 0:
            rows.append(_row(f"{sub_node_id}:direct", sub_node_id, sub["name"], "Sub Org", 2, own))

    for child_id in children:
        child = subs[child_id]
        rows.append(
            _row(
                f"sub:{child_id}",
                sub_node_id,
                child["name"],
                _TYPE_LABEL.get(child["entity_type"], child["entity_type"]),
                2,
                child["values"],
            )
        )

    return rows


def _emit_bge_rows(
    bge_id: int,
    bge: dict[str, Any],
    level1: list[int],
    subs: dict[int, dict[str, Any]],
    children_by_parent: dict[int, list[int]],
    direct_by_source: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    """Rows for one BGE: the roll-up (or leaf) BGE row, its sub-org / designee
    tree, and — when present — the direct-spend residue lines (one per source)."""
    bge_node_id = f"bge:{bge_id}"
    rows: list[dict[str, Any]] = []

    # With nested sub-orgs / service designees the BGE row rolls them up; with
    # none it's a plain BGE leaf. Either way the type is just "BGE" — the roll-up
    # is a summary, not a distinct type.
    rows.append(_row(bge_node_id, None, bge["name"], "BGE", 0, bge["values"]))

    # Direct-spend residue lines lead the BGE's nested rows, before the sub-org /
    # designee tree. Only split when there are sub-entities to allocate against; a
    # leaf BGE already shows all its spend in its own row.
    if level1:
        rows.extend(_residue_rows(bge_node_id, bge, direct_by_source))

    for sub_id in level1:
        rows.extend(_emit_level1_rows(bge_node_id, sub_id, subs, children_by_parent))

    return rows


def build_summary_result(
    dataset_id: str,
    df: pd.DataFrame,
    scaffold_df: pd.DataFrame,
    filters: Filters,
) -> DatasetResult:
    categories = [{"code": code, "name": name} for code, name in CATEGORY_ORDER]

    # Seed the table from the full predefined hierarchy, then overlay spend, so
    # every BGE / sub_bge / SD shows up even with no data for the period.
    bges, subs = _scaffold(scaffold_df)
    # bge_id -> source_group -> values: BGE-direct spend split by source family,
    # used to break the "extra" residue line into TSMA vs NGTA.
    direct: dict[int, dict[str, dict[str, float]]] = {}
    if not df.empty:
        _aggregate(df, bges, subs, direct)

    # Service Designees grouped by their parent Sub-org.
    children_by_parent: dict[int, list[int]] = defaultdict(list)
    for sub_id, sub in subs.items():
        if sub["entity_type"] == "service_designee" and sub["parent_sub_bge_id"] is not None:
            children_by_parent[sub["parent_sub_bge_id"]].append(sub_id)

    # Level-1 nodes under each BGE: Sub-orgs, plus Service Designees with no parent.
    level1_by_bge: dict[int, list[int]] = defaultdict(list)
    for sub_id, sub in subs.items():
        if sub["entity_type"] == "sub_org" or sub["parent_sub_bge_id"] is None:
            level1_by_bge[sub["bge_id"]].append(sub_id)

    # Sort by spend (desc), name (asc) as a tiebreaker so the many zero-spend
    # entities land in a stable, alphabetical order below the ones with data.
    table_rows: list[dict[str, Any]] = []
    for bge_id in sorted(bges, key=lambda b: (-_total(bges[b]["values"]), bges[b]["name"])):
        level1 = sorted(
            level1_by_bge.get(bge_id, ()),
            key=lambda s: (-_total(_display_values(subs, children_by_parent, s)), subs[s]["name"]),
        )
        table_rows.extend(
            _emit_bge_rows(
                bge_id, bges[bge_id], level1, subs, children_by_parent, direct.get(bge_id, {})
            )
        )

    grand_total = sum(_total(bges[b]["values"]) for b in bges)

    tabular_rows = [
        [
            row["name"],
            row["type"],
            row["level"],
            *[row["values"][code] for code in CATEGORY_CODES],
            row["total"],
        ]
        for row in table_rows
    ]

    return DatasetResult(
        columns=RESULT_COLUMNS,
        rows=tabular_rows,
        row_count=len(tabular_rows),
        metadata={
            "dataset": dataset_id,
            "filters": filters.model_dump(mode="json"),
            "table": {
                "categories": categories,
                "rows": table_rows,
                "total_millions": round(grand_total, 6),
            },
        },
    )
