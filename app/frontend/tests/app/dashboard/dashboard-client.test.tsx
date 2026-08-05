import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Drive each chart's query state independently, keyed by the first queryKey
// entry, and capture each query's queryFn so tests can exercise the data layer.
const { queryStates, queryFns } = vi.hoisted(() => ({
  queryStates: {} as Record<
    string,
    { data?: unknown; isLoading?: boolean; isError?: boolean }
  >,
  queryFns: {} as Record<string, () => Promise<unknown>>,
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: (opts: { queryKey: [string, ...unknown[]]; queryFn: () => Promise<unknown> }) => {
    const key = opts.queryKey[0];
    queryFns[key] = opts.queryFn;
    return (
      queryStates[key] ?? { data: undefined, isLoading: false, isError: false }
    );
  },
}));

// Heavy / environment-specific dependencies reduced to inert stubs.
vi.mock("next/dynamic", () => ({ default: () => () => null }));
vi.mock("next/link", () => ({
  default: ({ children }: { children?: React.ReactNode }) => <>{children}</>,
}));
vi.mock("lucide-react", () => ({ UserCircle2: () => null }));
vi.mock("@bcgov/design-system-react-components", () => ({
  Header: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
  Heading: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
  AlertBanner: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
}));
vi.mock("@/components/dashboard-sidebar", () => ({ DashboardSidebar: () => null }));
vi.mock("@/components/minimal-footer", () => ({ MinimalFooter: () => null }));
vi.mock("@/components/spend-indicator-cards", () => ({
  SpendIndicatorCards: () => null,
}));
vi.mock("@/components/spend-timeline-brush", () => ({
  SpendTimelineBrush: ({ onPeriodsChange }: { onPeriodsChange: (p: string[]) => void }) => (
    <button
      data-testid="select-periods"
      onClick={() => onPeriodsChange(["2024_1", "2024_2"])}
    >
      select periods
    </button>
  ),
}));
// Each chart component renders its own header, tabs and states and has its own
// tests; these stubs just expose the props the dashboard passes down.
const { chartStub } = vi.hoisted(() => ({
  chartStub: (testId: string) => (props: Record<string, unknown>) => (
    <div
      data-testid={testId}
      data-has-data={props.chart ?? props.table ? "yes" : "no"}
      data-loading={props.isLoading ? "yes" : "no"}
      data-error={props.isError ? "yes" : "no"}
      data-date-range={String(props.dateRangeLabel ?? "")}
    />
  ),
}));

vi.mock("@/components/spend-by-category", () => ({
  SpendByCategory: chartStub("category-chart"),
}));
vi.mock("@/components/spend-by-sector", () => ({
  SpendBySector: chartStub("sector-chart"),
}));
vi.mock("@/components/spend-by-bge", () => ({
  SpendByBge: chartStub("bge-chart"),
}));
vi.mock("@/components/spend-summary-table", () => ({
  SpendSummaryTable: chartStub("summary-table"),
}));

import { DashboardClient } from "@/app/dashboard/dashboard-client";

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeEach(() => {
  for (const key of Object.keys(queryStates)) delete queryStates[key];
  for (const key of Object.keys(queryFns)) delete queryFns[key];
  vi.stubGlobal("ResizeObserver", ResizeObserverStub);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function renderDashboard(visibleDatasetIds: string[]) {
  return render(
    <DashboardClient displayName="Alice" visibleDatasetIds={visibleDatasetIds} />,
  );
}

describe("DashboardClient dataset access gating", () => {
  it("always shows the service category and sector cards", () => {
    renderDashboard([]);

    expect(screen.getByTestId("category-chart")).toBeInTheDocument();
    expect(screen.getByTestId("sector-chart")).toBeInTheDocument();
  });

  it("hides the BGE and summary cards when those datasets are not visible", () => {
    renderDashboard([]);

    expect(screen.queryByTestId("bge-chart")).not.toBeInTheDocument();
    expect(screen.queryByTestId("summary-table")).not.toBeInTheDocument();
  });

  it("shows the BGE card when the dataset is visible to the user", () => {
    renderDashboard(["spend-by-bge"]);
    expect(screen.getByTestId("bge-chart")).toBeInTheDocument();
  });

  it("shows the summary card when the dataset is visible to the user", () => {
    renderDashboard(["spend-summary"]);
    expect(screen.getByTestId("summary-table")).toBeInTheDocument();
  });
});

describe("DashboardClient query state hand-off", () => {
  it("passes the loading flag to the card", () => {
    queryStates["spend-by-bge"] = { isLoading: true };
    renderDashboard(["spend-by-bge"]);

    expect(screen.getByTestId("bge-chart")).toHaveAttribute("data-loading", "yes");
  });

  it("passes the error flag to the card", () => {
    queryStates["spend-by-bge"] = { isError: true };
    renderDashboard(["spend-by-bge"]);

    expect(screen.getByTestId("bge-chart")).toHaveAttribute("data-error", "yes");
  });

  it("passes no chart when the query returned none", () => {
    queryStates["spend-by-bge"] = { data: undefined };
    renderDashboard(["spend-by-bge"]);

    expect(screen.getByTestId("bge-chart")).toHaveAttribute("data-has-data", "no");
  });

  it("passes the chart down once data is available", () => {
    queryStates["spend-by-bge"] = { data: { data: [] } };
    renderDashboard(["spend-by-bge"]);

    expect(screen.getByTestId("bge-chart")).toHaveAttribute("data-has-data", "yes");
  });

  it("passes the summary table down", () => {
    queryStates["spend-summary"] = { data: { rows: [] } };
    renderDashboard(["spend-summary"]);

    expect(screen.getByTestId("summary-table")).toHaveAttribute(
      "data-has-data",
      "yes",
    );
  });
});

function stubFetch(chart: unknown, ok = true, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok,
      status,
      json: async () => ({ metadata: { chart } }),
    }),
  );
}

describe("DashboardClient query functions (data layer)", () => {
  beforeEach(() => renderDashboard(["spend-by-bge"]));

  it("service-category query returns the plotly chart when valid", async () => {
    stubFetch({ data: [], layout: {} });
    expect(await queryFns["service-category-spend"]()).toEqual({
      plotly: { data: [], layout: {} },
    });
  });

  it("service-category query returns null plotly for a non-plotly payload", async () => {
    stubFetch({ not: "plotly" });
    expect(await queryFns["service-category-spend"]()).toEqual({ plotly: null });
  });

  it("indicator query returns the chart when valid, else null", async () => {
    stubFetch({ indicators: [{ label: "x", value_millions: 1 }] });
    expect(await queryFns["isp-spend-indicators"]()).toEqual({
      indicators: [{ label: "x", value_millions: 1 }],
    });
    stubFetch({});
    expect(await queryFns["isp-spend-indicators"]()).toBeNull();
  });

  it("timeline query keeps only periods from 2024 onward", async () => {
    stubFetch({
      valueLabel: "Spend",
      data: [
        { period: "2023_4", label: "L0", value: 1 },
        { period: "2024_1", label: "L1", value: 2 },
        { period: "2025_2", label: "L2", value: 3 },
      ],
    });
    const result = (await queryFns["total-spend-over-time"]()) as {
      data: { period: string }[];
    };
    expect(result.data.map((p) => p.period)).toEqual(["2024_1", "2025_2"]);
  });

  it("timeline query returns null for a non-timeline payload", async () => {
    stubFetch(null);
    expect(await queryFns["total-spend-over-time"]()).toBeNull();
  });

  it("sector and bge queries return their charts when valid, else null", async () => {
    stubFetch({ data: [], total_millions: 0, dataKey: "spend_millions", nameKey: "sector" });
    expect(await queryFns["spend-by-sector"]()).toMatchObject({ dataKey: "spend_millions" });

    stubFetch({ data: [], vendors: ["TELUS"], total_millions: 0 });
    expect(await queryFns["spend-by-bge"]()).toMatchObject({ vendors: ["TELUS"] });

    stubFetch({ invalid: true });
    expect(await queryFns["spend-by-sector"]()).toBeNull();
    expect(await queryFns["spend-by-bge"]()).toBeNull();
  });

  it("propagates a failed dataset request", async () => {
    stubFetch({}, false, 500);
    await expect(queryFns["spend-by-sector"]()).rejects.toThrow(/status 500/);
  });
});

describe("DashboardClient charts, labels and interactions", () => {
  it("unwraps the plotly chart before passing it to the category card", () => {
    queryStates["service-category-spend"] = {
      data: { plotly: { data: [{ name: "TELUS", x: [1], text: ["a"] }], layout: { legend: {} } } },
    };
    renderDashboard([]);

    expect(screen.getByTestId("category-chart")).toHaveAttribute(
      "data-has-data",
      "yes",
    );
  });

  it("tells the category card when its query errored", () => {
    queryStates["service-category-spend"] = { isError: true };
    renderDashboard([]);

    expect(screen.getByTestId("category-chart")).toHaveAttribute(
      "data-error",
      "yes",
    );
  });

  it("passes the sector chart to the sector card", () => {
    queryStates["spend-by-sector"] = { data: { total_millions: 12.34 } };
    renderDashboard([]);

    expect(screen.getByTestId("sector-chart")).toHaveAttribute(
      "data-has-data",
      "yes",
    );
  });

  it("logs the user out when the logout button is clicked", () => {
    vi.stubGlobal("location", { href: "" });
    renderDashboard([]);

    fireEvent.click(screen.getByRole("button", { name: "Logout" }));

    expect(globalThis.location.href).toBe("/auth/logout");
  });

  it("passes the selected period range to the cards", () => {
    renderDashboard([]);

    fireEvent.click(screen.getByTestId("select-periods"));

    expect(screen.getByTestId("sector-chart")).toHaveAttribute(
      "data-date-range",
      "(Q1 FY2024 – Q2 FY2024)",
    );
  });
});
