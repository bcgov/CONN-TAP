"""Tests for the spend-summary table builder."""
from types import SimpleNamespace

from app.datasets.spend_summary.helpers import CATEGORY_CODES, build_summary_result


class FakeFrame:
    def __init__(self, records):
        self.records = records

    @property
    def empty(self):
        return not self.records

    def itertuples(self, index=False):
        return (SimpleNamespace(**r) for r in self.records)


class FakeFilters:
    def model_dump(self, mode="python"):
        return {"year_type": "fiscal", "period": None}


def scaffold_row(bge_id, bge_name, sub_id=None, sub_name=None, kind=None, parent=None):
    return {
        "bge_id": bge_id,
        "bge_code": f"B{bge_id}",
        "bge_name": bge_name,
        "sub_bge_id": sub_id,
        "sub_bge_name": sub_name,
        "entity_type": kind,
        "parent_sub_bge_id": parent,
    }


def spend_row(
    bge_id, bge_name, category, millions,
    sub_id=None, sub_name=None, kind=None, parent=None, source_group="ngta",
):
    return {
        "bge_id": bge_id,
        "bge_code": f"B{bge_id}",
        "bge_name": bge_name,
        "service_category_code": category,
        "spend_millions": millions,
        "sub_bge_id": sub_id,
        "sub_bge_name": sub_name,
        "entity_type": kind,
        "parent_sub_bge_id": parent,
        "source_group": source_group,
    }


# Alpha exercises the full tree: a sub-org with two designees and its own
# residual spend, a childless sub-org, a parentless designee that sits at level 1,
# a scaffold-only sub-org with no spend, and BGE-level spend booked to no sub-org
# (split across NGTA + TSMA sources). Beta is a leaf BGE (spend, no sub-orgs).
# Gamma is scaffold-only.
SCAFFOLD = FakeFrame([
    scaffold_row(1, "Alpha", 10, "Sub A", "sub_org"),
    scaffold_row(1, "Alpha", 100, "Des A1", "service_designee", parent=10),
    scaffold_row(1, "Alpha", 101, "Des A2", "service_designee", parent=10),
    scaffold_row(1, "Alpha", 11, "Sub B", "sub_org"),
    scaffold_row(1, "Alpha", 12, "Lone SD", "service_designee"),
    scaffold_row(1, "Alpha", 13, "Sub Zero", "sub_org"),
    scaffold_row(2, "Beta"),
    scaffold_row(3, "Gamma"),
])
SPEND = FakeFrame([
    spend_row(1, "Alpha", "voice", 5.0, 10, "Sub A", "sub_org"),
    spend_row(1, "Alpha", "data", 10.0, 100, "Des A1", "service_designee", parent=10),
    spend_row(1, "Alpha", "voice", 2.0, 100, "Des A1", "service_designee", parent=10),
    spend_row(1, "Alpha", "cellular", 3.0, 101, "Des A2", "service_designee", parent=10),
    spend_row(1, "Alpha", "temporary_services", 4.0, 11, "Sub B", "sub_org"),
    spend_row(1, "Alpha", "other_professional_services", 6.0, 12, "Lone SD", "service_designee"),
    # BGE-direct spend (no sub_bge), split across the two source families so the
    # residue becomes two "BGE" lines: 0.6 NGTA + 0.4 TSMA = 1.0 total voice.
    spend_row(1, "Alpha", "voice", 0.6, source_group="ngta"),
    spend_row(1, "Alpha", "voice", 0.4, source_group="tsma"),
    spend_row(2, "Beta", "data", 20.0),
])


def build(spend=SPEND, scaffold=SCAFFOLD):
    return build_summary_result("spend-summary", spend, scaffold, FakeFilters())


def rows_by_id(result):
    return {r["id"]: r for r in result.metadata["table"]["rows"]}


def test_build_summary_table():
    result = build()
    table = result.metadata["table"]
    rows = rows_by_id(result)

    assert [c["code"] for c in table["categories"]] == list(CATEGORY_CODES)
    assert table["total_millions"] == 51.0  # 31 under Alpha + 20 under Beta

    alpha = rows["bge:1"]
    assert alpha["type"] == "BGE"
    assert alpha["level"] == 0
    assert alpha["parent_id"] is None
    assert alpha["values"] == {
        "voice": 8.0,  # 5 Sub A + 2 Des A1 + 1 direct
        "data": 10.0,
        "cellular": 3.0,
        "other_professional_services": 6.0,
        "temporary_services": 4.0,
    }
    assert alpha["total"] == 31.0

    assert rows["bge:2"]["values"]["data"] == 20.0
    assert rows["bge:2"]["total"] == 20.0

    # A sub-org rolls up its own spend plus its designee children.
    sub_a = rows["sub:10"]
    assert sub_a["type"] == "Sub Org"
    assert sub_a["level"] == 1
    assert sub_a["parent_id"] == "bge:1"
    assert sub_a["values"]["voice"] == 7.0  # 5 own + 2 from Des A1
    assert sub_a["values"]["data"] == 10.0
    assert sub_a["total"] == 20.0

    des = rows["sub:100"]
    assert des["type"] == "Service Designee"
    assert des["level"] == 2
    assert des["parent_id"] == "sub:10"
    assert des["values"]["data"] == 10.0
    assert rows["sub:101"]["values"]["cellular"] == 3.0

    # Sub A's own spend that isn't under a designee shows as a residue row.
    residue = rows["sub:10:direct"]
    assert residue["type"] == "Sub Org"
    assert residue["level"] == 2
    assert residue["values"]["voice"] == 5.0

    # A parentless designee is promoted to level 1 under the BGE.
    lone = rows["sub:12"]
    assert lone["type"] == "Service Designee"
    assert lone["level"] == 1
    assert lone["parent_id"] == "bge:1"
    assert lone["values"]["other_professional_services"] == 6.0

    # Childless sub-org: a plain level-1 row, no residue.
    assert rows["sub:11"]["values"]["temporary_services"] == 4.0
    assert "sub:11:direct" not in rows

    # BGE spend not booked to any sub-org becomes a BGE residue row per source
    # family, each labelled with the source and summing back to the direct total.
    direct_ngta = rows["bge:1:direct:ngta"]
    assert direct_ngta["type"] == "BGE"
    assert direct_ngta["level"] == 1
    assert direct_ngta["name"] == "Alpha (NGTA)"
    assert direct_ngta["values"]["voice"] == 0.6

    direct_tsma = rows["bge:1:direct:tsma"]
    assert direct_tsma["type"] == "BGE"
    assert direct_tsma["level"] == 1
    assert direct_tsma["name"] == "Alpha (TSMA)"
    assert direct_tsma["values"]["voice"] == 0.4


def test_zero_spend_entities_still_appear():
    rows = rows_by_id(build())

    gamma = rows["bge:3"]
    assert gamma["name"] == "Gamma"
    assert gamma["total"] == 0.0
    assert set(gamma["values"].values()) == {0.0}

    assert rows["sub:13"]["type"] == "Sub Org"
    assert rows["sub:13"]["total"] == 0.0


def test_rows_sorted_by_spend_then_name():
    ids = [r["id"] for r in build().metadata["table"]["rows"]]

    # BGEs: Alpha (31) > Beta (20) > Gamma (0).
    assert ids.index("bge:1") < ids.index("bge:2") < ids.index("bge:3")

    # Alpha's direct-spend residue lines lead its nested rows, before any sub-org.
    assert ids[ids.index("bge:1") + 1:ids.index("bge:1") + 3] == ["bge:1:direct:ngta", "bge:1:direct:tsma"]
    assert ids.index("bge:1:direct:tsma") < ids.index("sub:10")

    # Level-1 nodes under Alpha: Sub A (20) > Lone SD (6) > Sub B (4) > Sub Zero (0).
    level1 = [i for i in ids if i in {"sub:10", "sub:12", "sub:11", "sub:13"}]
    assert level1 == ["sub:10", "sub:12", "sub:11", "sub:13"]

    # A sub-org's own-spend residue leads its children, all before the next sibling.
    assert ids[ids.index("sub:10") + 1:ids.index("sub:12")] == ["sub:10:direct", "sub:100", "sub:101"]


def test_flat_rows_match_nested_table():
    result = build()

    assert result.columns == ["entity_name", "entity_type", "level", *CATEGORY_CODES, "total_millions"]
    assert result.row_count == len(result.rows) == len(result.metadata["table"]["rows"])

    alpha = next(r for r in result.rows if r[0] == "Alpha" and r[2] == 0)
    assert alpha[3] == 8.0  # voice
    assert alpha[-1] == 31.0  # total


def test_metadata():
    result = build()
    assert result.metadata["dataset"] == "spend-summary"
    assert result.metadata["filters"] == {"year_type": "fiscal", "period": None}


def test_empty_spend():
    table = build(spend=FakeFrame([])).metadata["table"]

    assert table["total_millions"] == 0.0
    assert all(r["total"] == 0.0 for r in table["rows"])

    ids = {r["id"] for r in table["rows"]}
    assert {"bge:1", "bge:2", "bge:3", "sub:10", "sub:100", "sub:12"} <= ids
    assert not any(":direct" in i for i in ids)  # nothing left over (incl. per-source BGE residue)


def test_no_data_at_all():
    result = build(spend=FakeFrame([]), scaffold=FakeFrame([]))
    assert result.rows == []
    assert result.row_count == 0
    assert result.metadata["table"]["total_millions"] == 0.0
