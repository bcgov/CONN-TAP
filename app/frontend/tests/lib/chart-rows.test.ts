import { describe, expect, it } from "vitest";

import {
  bgeRowsWithTotals,
  plotlyCategoryRows,
  type BgeChart,
  type PlotlyChart,
} from "@/lib/chart-utils";

function makeBgeChart(): BgeChart {
  return {
    vendors: ["TELUS", "Rogers"],
    total_millions: 30,
    data: [
      { bge_code: "A", organization_name: "Org A", TELUS: 10, Rogers: 5 },
      { bge_code: "B", organization_name: "Org B", TELUS: 8, Rogers: 7 },
    ],
  };
}

describe("bgeRowsWithTotals", () => {
  it("adds each row's vendor spend as _total", () => {
    expect(bgeRowsWithTotals(makeBgeChart()).map((row) => row._total)).toEqual([
      15, 15,
    ]);
  });

  it("drops rows with no spend", () => {
    const chart: BgeChart = {
      ...makeBgeChart(),
      data: [
        { bge_code: "A", organization_name: "Org A", TELUS: 10, Rogers: 5 },
        { bge_code: "Z", organization_name: "Org Z", TELUS: 0, Rogers: 0 },
      ],
    };

    expect(bgeRowsWithTotals(chart).map((row) => row.bge_code)).toEqual(["A"]);
  });

  it("treats a missing vendor value as zero", () => {
    const chart: BgeChart = {
      ...makeBgeChart(),
      data: [{ bge_code: "A", organization_name: "Org A", TELUS: 4 }],
    };

    expect(bgeRowsWithTotals(chart)[0]._total).toBe(4);
  });

  it("returns nothing for an empty chart", () => {
    expect(bgeRowsWithTotals({ ...makeBgeChart(), data: [] })).toEqual([]);
  });
});

function makeCategoryChart(): PlotlyChart {
  return {
    layout: {},
    data: [
      { type: "bar", name: "TELUS", x: ["Voice", "Data"], y: [10, 4] },
      { type: "bar", name: "Rogers", x: ["Voice"], y: [2] },
    ] as PlotlyChart["data"],
  };
}

describe("plotlyCategoryRows", () => {
  it("lists the providers in trace order", () => {
    expect(plotlyCategoryRows(makeCategoryChart()).providers).toEqual([
      "TELUS",
      "Rogers",
    ]);
  });

  it("builds a row per category with each provider's spend and a total", () => {
    expect(plotlyCategoryRows(makeCategoryChart()).rows).toEqual([
      { category: "Voice", TELUS: 10, Rogers: 2, total: 12 },
      // Rogers has no "Data" point, so it counts as zero.
      { category: "Data", TELUS: 4, Rogers: 0, total: 4 },
    ]);
  });

  it("drops categories where nothing was spent", () => {
    const chart: PlotlyChart = {
      layout: {},
      data: [
        { type: "bar", name: "TELUS", x: ["Voice", "Data"], y: [10, 0] },
      ] as PlotlyChart["data"],
    };

    expect(plotlyCategoryRows(chart).rows.map((row) => row.category)).toEqual([
      "Voice",
    ]);
  });

  it("returns nothing for a chart with no traces", () => {
    expect(plotlyCategoryRows({ layout: {}, data: [] })).toEqual({
      providers: [],
      rows: [],
    });
  });
});
