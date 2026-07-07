import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { SectorChart } from "@/lib/chart-utils";
import { SpendBySectorChart } from "@/components/spend-by-sector-chart";

// Capture the render-prop callbacks recharts is configured with so we can
// exercise the legend/tooltip logic without a real layout.
const captured: {
  legendContent?: (props: { payload?: { value?: string; color?: string }[] }) => React.ReactNode;
  tooltipFormatter?: (spend: unknown, sector: unknown) => [string, string];
} = {};

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
  PieChart: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
  Pie: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
  Sector: () => null,
  Tooltip: (props: { formatter: (s: unknown, n: unknown) => [string, string] }) => {
    captured.tooltipFormatter = props.formatter;
    return null;
  },
  Legend: (props: {
    content: (p: { payload?: { value?: string; color?: string }[] }) => React.ReactNode;
  }) => {
    captured.legendContent = props.content;
    return <>{props.content({ payload: legendPayload })}</>;
  },
  type: {},
}));

let legendPayload: { value?: string; color?: string }[] = [];

function makeChart(): SectorChart {
  return {
    dataKey: "spend_millions",
    nameKey: "sector",
    total_millions: 30,
    data: [
      { sector: "Gov & ECC", spend_millions: 12, percentage: 40, fill: "#FCBA19" },
      { sector: "School Districts", spend_millions: 18, percentage: 60, fill: "#7b5ea7" },
    ],
  };
}

describe("SpendBySectorChart", () => {
  it("renders the loading state", () => {
    render(<SpendBySectorChart chart={makeChart()} isLoading />);
    expect(screen.getByText("Loading chart…")).toBeInTheDocument();
  });

  it("renders the empty state when there is no data", () => {
    const chart = { ...makeChart(), data: [] };
    render(<SpendBySectorChart chart={chart} />);
    expect(screen.getByText("No data for this period.")).toBeInTheDocument();
  });

  it("renders the date range label when provided", () => {
    render(<SpendBySectorChart chart={makeChart()} dateRangeLabel="FY2024 Q1" />);
    expect(screen.getByText("FY2024 Q1")).toBeInTheDocument();
  });

  it("shows friendly sector display names in the legend with percentage and spend", () => {
    legendPayload = [
      { value: "Gov & ECC", color: "#FCBA19" },
      { value: "School Districts", color: "#7b5ea7" },
    ];
    render(<SpendBySectorChart chart={makeChart()} />);

    // "Gov & ECC" is mapped to the shorter "Gov BC" display name.
    expect(screen.getByText(/Gov BC = 40% \(\$12M\)/)).toBeInTheDocument();
    // A sector without a mapping keeps its original name.
    expect(screen.getByText(/School Districts = 60% \(\$18M\)/)).toBeInTheDocument();
  });

  it("maps the tooltip label through displaySector and includes spend + percentage", () => {
    render(<SpendBySectorChart chart={makeChart()} />);

    expect(captured.tooltipFormatter?.(12, "Gov & ECC")).toEqual([
      "$12M (40%)",
      "Gov BC",
    ]);
    expect(captured.tooltipFormatter?.(18, "School Districts")).toEqual([
      "$18M (60%)",
      "School Districts",
    ]);
  });
});
