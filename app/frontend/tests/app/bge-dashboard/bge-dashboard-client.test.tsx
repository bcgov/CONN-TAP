import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Each query's data is set per test, keyed by the first queryKey entry. The
// queryFns are kept so the data layer can be tested too.
const { queryData, queryFns } = vi.hoisted(() => ({
  queryData: {} as Record<string, unknown>,
  queryFns: {} as Record<string, () => Promise<unknown>>,
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: (opts: { queryKey: [string, ...unknown[]]; queryFn: () => Promise<unknown> }) => {
    queryFns[opts.queryKey[0]] = opts.queryFn;
    return { data: queryData[opts.queryKey[0]] };
  },
}));
vi.mock("next/navigation", () => ({ usePathname: () => "/bge-dashboard" }));

import { BgeDashboardClient } from "@/app/bge-dashboard/bge-dashboard-client";

const MONTHLY_SPEND = [
  { period: "2026-04", label: "Apr 2026", value: 0.5 },
  { period: "2026-05", label: "May 2026", value: 0.9 },
  { period: "2026-06", label: "Jun 2026", value: 0.7 },
];

const INDICATORS = {
  indicators: [
    { label: "Total TSMA & NGTA Spend", value_millions: 2 },
    { label: "Total TELUS Spend", value_millions: 1.5, provider: "TELUS" },
    { label: "Total Rogers Spend", value_millions: 0.5, provider: "Rogers" },
  ],
};

const jsonResponse = (body: unknown) => ({ ok: true, json: async () => body }) as Response;

beforeEach(() => {
  for (const key of Object.keys(queryData)) delete queryData[key];
  for (const key of Object.keys(queryFns)) delete queryFns[key];
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("BgeDashboardClient", () => {
  it("shows the user's organization in the header", () => {
    render(<BgeDashboardClient displayName="Alice" orgName="Ministry of Health" />);

    expect(screen.getByText("Ministry of Health")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Telecom Spend Dashboard" })).toBeInTheDocument();
  });

  it("shows dashes before the data has loaded", () => {
    render(<BgeDashboardClient displayName="Alice" />);

    expect(screen.getByText("Reporting Period: –")).toBeInTheDocument();
    expect(screen.getAllByText("—")).toHaveLength(2); // total spend and peak month
  });

  it("shows the reporting period, total spend, provider split and peak month", () => {
    queryData["monthly-spend"] = MONTHLY_SPEND;
    queryData["isp-spend-indicators"] = INDICATORS;
    render(<BgeDashboardClient displayName="Alice" />);

    expect(screen.getByText("Reporting Period: Apr 2026 – Jun 2026")).toBeInTheDocument();
    expect(screen.getByText("$2M")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("25%")).toBeInTheDocument();
    expect(screen.getByText("May 2026")).toBeInTheDocument();
    expect(screen.getByText("$900,000")).toBeInTheDocument();
  });

  it("shows 0% for each provider when the total is zero", () => {
    queryData["monthly-spend"] = MONTHLY_SPEND;
    queryData["isp-spend-indicators"] = {
      indicators: [{ label: "Total TELUS Spend", value_millions: 0, provider: "TELUS" }],
    };
    render(<BgeDashboardClient displayName="Alice" />);

    expect(screen.getByText("0%")).toBeInTheDocument();
  });
});

describe("BgeDashboardClient data layer", () => {
  beforeEach(() => {
    queryData["monthly-spend"] = MONTHLY_SPEND;
    render(<BgeDashboardClient displayName="Alice" />);
  });

  it("monthly spend query returns the months, or none for another chart type", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({ metadata: { chart: { data: MONTHLY_SPEND } } })));
    await expect(queryFns["monthly-spend"]()).resolves.toEqual(MONTHLY_SPEND);

    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({ metadata: { chart: {} } })));
    await expect(queryFns["monthly-spend"]()).resolves.toEqual([]);
  });

  it("spend query asks for the reporting period and returns the chart, or null", async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ metadata: { chart: INDICATORS } }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(queryFns["isp-spend-indicators"]()).resolves.toEqual(INDICATORS);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/datasets/isp-spend-indicators/data?period=2026-04&period=2026-05&period=2026-06",
      { cache: "no-store" },
    );

    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({ metadata: { chart: {} } })));
    await expect(queryFns["isp-spend-indicators"]()).resolves.toBeNull();
  });
});
