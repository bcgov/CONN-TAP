import { describe, expect, it } from "vitest";

import { isSummaryTable, type SummaryTable } from "@/lib/chart-utils";

const validTable: SummaryTable = {
  categories: [{ code: "A", name: "Alpha" }],
  providers: ["TELUS", "Rogers"],
  rows: [
    {
      id: "1",
      parent_id: null,
      name: "Root",
      type: "BGE",
      level: 0,
      values: { A: 1 },
      total: 1,
    },
  ],
  total_millions: 1,
};

describe("isSummaryTable", () => {
  it("accepts a valid summary table", () => {
    expect(isSummaryTable(validTable)).toBe(true);
  });

  it("rejects non-objects", () => {
    expect(isSummaryTable(null)).toBe(false);
    expect(isSummaryTable(undefined)).toBe(false);
    expect(isSummaryTable("table")).toBe(false);
  });

  it("rejects objects missing categories or rows", () => {
    expect(isSummaryTable({ rows: [] })).toBe(false);
    expect(isSummaryTable({ categories: [] })).toBe(false);
  });

  it("rejects when categories or rows are not arrays", () => {
    expect(isSummaryTable({ categories: {}, rows: [] })).toBe(false);
    expect(isSummaryTable({ categories: [], rows: {} })).toBe(false);
  });
});
