import { afterEach, describe, expect, it, vi } from "vitest";

import { formatPeriodRange } from "@/lib/date-utils";
import { fetchDataset } from "@/lib/fetch-dataset";

describe("fetchDataset", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("requests the dataset with one period parameter per period", async () => {
    const body = { metadata: { chart: { indicators: [] } } };
    const fetchMock = vi.fn(async () => ({ ok: true, json: async () => body }) as Response);
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchDataset("isp-spend-indicators", { period: ["2026-01", "2026-02"] });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/datasets/isp-spend-indicators/data?period=2026-01&period=2026-02",
      { cache: "no-store" },
    );
    expect(result).toEqual(body);
  });

  it("throws when the request fails", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 403 }) as Response));

    await expect(fetchDataset("spend-by-bge")).rejects.toThrow("status 403");
  });
});

describe("formatPeriodRange", () => {
  it("shows the first and last month", () => {
    expect(formatPeriodRange(["2025-10", "2025-11", "2026-10"])).toBe("Oct 2025 – Oct 2026");
  });

  it("shows a single month once", () => {
    expect(formatPeriodRange(["2026-06"])).toBe("Jun 2026");
  });

  it("is empty when there are no periods", () => {
    expect(formatPeriodRange([])).toBe("");
  });
});
