import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Drive each chart's query state independently, keyed by the first queryKey entry.
const { queryStates } = vi.hoisted(() => ({
  queryStates: {} as Record<
    string,
    { data?: unknown; isLoading?: boolean; isError?: boolean }
  >,
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: (opts: { queryKey: unknown[] }) =>
    queryStates[String(opts.queryKey[0])] ?? {
      data: undefined,
      isLoading: false,
      isError: false,
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
  SpendTimelineBrush: () => null,
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
  vi.stubGlobal("ResizeObserver", ResizeObserverStub);
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
