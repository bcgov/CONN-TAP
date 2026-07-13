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
vi.mock("@/components/spend-by-sector-chart", () => ({
  SpendBySectorChart: () => <div data-testid="sector-chart" />,
}));
vi.mock("@/components/spend-by-bge-chart", () => ({
  SpendByBgeChart: () => <div data-testid="bge-chart" />,
}));
vi.mock("@/components/custom-dashboard-chart", () => ({
  CustomDashboardChart: ({ children }: { children?: React.ReactNode }) => (
    <div>{children}</div>
  ),
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

describe("DashboardClient BGE access gating", () => {
  it("hides the Spend by BGE card when the dataset is not visible to the user", () => {
    renderDashboard([]);

    expect(screen.queryByText("Spend by BGE")).not.toBeInTheDocument();
    expect(screen.queryByTestId("bge-chart")).not.toBeInTheDocument();
  });

  it("shows the Spend by BGE card when the dataset is visible to the user", () => {
    renderDashboard(["spend-by-bge"]);

    expect(screen.getByText("Spend by BGE")).toBeInTheDocument();
  });
});

describe("DashboardClient ChartState rendering (BGE card)", () => {
  it("renders the loading label while the BGE query loads", () => {
    queryStates["spend-by-bge"] = { isLoading: true };
    renderDashboard(["spend-by-bge"]);

    expect(screen.getByText("Loading BGE chart…")).toBeInTheDocument();
    expect(screen.queryByTestId("bge-chart")).not.toBeInTheDocument();
  });

  it("renders the error label when the BGE query fails", () => {
    queryStates["spend-by-bge"] = { isError: true };
    renderDashboard(["spend-by-bge"]);

    expect(screen.getByText("Unable to load BGE data.")).toBeInTheDocument();
  });

  it("renders the empty label when the BGE query returns no data", () => {
    queryStates["spend-by-bge"] = { data: undefined };
    renderDashboard(["spend-by-bge"]);

    // Sector and BGE cards both fall back to this label when data is absent.
    expect(screen.getAllByText("No data for this period.").length).toBeGreaterThan(0);
    expect(screen.queryByTestId("bge-chart")).not.toBeInTheDocument();
  });

  it("renders the BGE chart once data is available", () => {
    queryStates["spend-by-bge"] = { data: { data: [] } };
    renderDashboard(["spend-by-bge"]);

    expect(screen.getByTestId("bge-chart")).toBeInTheDocument();
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
  it("renders the plotly chart card when plotly data is present", () => {
    queryStates["service-category-spend"] = {
      data: { plotly: { data: [{ name: "TELUS", x: [1], text: ["a"] }], layout: { legend: {} } } },
    };
    renderDashboard([]);

    expect(screen.queryByText("No Plotly data for this period.")).not.toBeInTheDocument();
  });

  it("shows an alert when the service-category query errors", () => {
    queryStates["service-category-spend"] = { isError: true };
    renderDashboard([]);

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Unable to load service category spend data.",
    );
  });

  it("shows the sector total in the heading when sector data is present", () => {
    queryStates["spend-by-sector"] = { data: { total_millions: 12.34 } };
    renderDashboard([]);

    expect(
      screen.getByText(/Telecom Spend share by Sector \(\$12\.3M\)/),
    ).toBeInTheDocument();
  });

  it("changing the year type updates the select", () => {
    renderDashboard([]);
    const select = screen.getByRole("combobox");

    fireEvent.change(select, { target: { value: "calendar" } });

    expect(select).toHaveValue("calendar");
  });

  it("logs the user out when the logout button is clicked", () => {
    vi.stubGlobal("location", { href: "" });
    renderDashboard([]);

    fireEvent.click(screen.getByRole("button", { name: "Logout" }));

    expect(globalThis.location.href).toBe("/auth/logout");
  });

  it("shows the selected period range once periods are chosen", () => {
    renderDashboard([]);

    fireEvent.click(screen.getByTestId("select-periods"));

    expect(
      screen.getAllByText("(Q1 FY2024 – Q2 FY2024)").length,
    ).toBeGreaterThan(0);
  });
});
