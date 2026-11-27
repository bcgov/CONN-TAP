import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

const REPORTING_STATUS = {
  expected_count: 11,
  received_count: 8,
  missing: [
    { report: "Rogers Data", provider: "Rogers", service_type: "Wireline", frequency: "monthly", period: "May 2026" },
    { report: "TELUS", provider: "TELUS", service_type: "Wireless and Wireline", frequency: "monthly", period: "Jun 2026" },
    { report: "TSMA", provider: "TELUS", service_type: "", frequency: "quarterly", period: "Apr–Jun 2026" },
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
    expect(screen.getAllByText("—")).toHaveLength(3); // total spend, peak month and reporting status
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

  it("shows the reporting status and opens the pending NGTA and TSMA reports", async () => {
    const user = userEvent.setup();
    queryData["monthly-spend"] = MONTHLY_SPEND;
    queryData["reporting-status"] = REPORTING_STATUS;
    render(<BgeDashboardClient displayName="Alice" />);

    expect(screen.getByText("8 of 11 reports received")).toBeInTheDocument();
    expect(screen.getByText("3 Pending")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Reporting Status/ }));
    const details = screen.getByRole("dialog", { name: "Pending reports" });

    const ngta = within(details).getByRole("heading", { name: "Pending NGTA reports" }).closest("section")!;
    expect(
      within(ngta).getByText("Monthly reports not included in dashboard totals for Apr 2026 – Jun 2026"),
    ).toBeInTheDocument();
    expect(within(ngta).getAllByRole("columnheader").map((header) => header.textContent)).toEqual([
      "Provider",
      "Service type",
      "Reporting month",
      "Status",
    ]);
    expect(within(ngta).getByRole("row", { name: /Rogers Wireline May 2026 Pending/ })).toBeInTheDocument();
    expect(within(ngta).getByRole("row", { name: /TELUS Wireless and Wireline Jun 2026 Pending/ })).toBeInTheDocument();

    const tsma = within(details).getByRole("heading", { name: "Pending TSMA reports" }).closest("section")!;
    expect(
      within(tsma).getByText("Quarterly reports not included in dashboard totals for Apr 2026 – Jun 2026"),
    ).toBeInTheDocument();
    expect(within(tsma).getByRole("row", { name: /Apr–Jun 2026 Pending/ })).toBeInTheDocument();

    expect(within(details).queryByRole("heading", { name: "Pending TSMA Lite reports" })).not.toBeInTheDocument();
  });

  it("has nothing to open when every report is in", () => {
    queryData["monthly-spend"] = MONTHLY_SPEND;
    queryData["reporting-status"] = { expected_count: 11, received_count: 11, missing: [] };
    render(<BgeDashboardClient displayName="Alice" />);

    expect(screen.getByText("11 of 11 reports received")).toBeInTheDocument();
    expect(screen.getByText("Complete")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Reporting Status/ })).not.toBeInTheDocument();
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

  it("reporting status query asks for the reporting period and returns the counts", async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ metadata: REPORTING_STATUS }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(queryFns["reporting-status"]()).resolves.toEqual(REPORTING_STATUS);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/datasets/reporting-status/data?period=2026-04&period=2026-05&period=2026-06",
      { cache: "no-store" },
    );
  });
});
