import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { BgeChart } from "@/lib/chart-utils";
import { VENDOR_COLOURS } from "@/lib/chart-utils";
import { SpendByBge } from "@/components/spend-by-bge";

// Recharts needs a real layout to render; stub it so we can assert on the
// data/props the component builds rather than on SVG geometry.
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children?: React.ReactNode }) => (
    <div>{children}</div>
  ),
  BarChart: ({
    data,
    children,
  }: {
    data: { bge_code: string }[];
    children?: React.ReactNode;
  }) => (
    <div
      data-testid="barchart"
      data-rows={data.length}
      data-codes={data.map((d) => d.bge_code).join(",")}
    >
      {children}
    </div>
  ),
  Bar: ({
    dataKey,
    fill,
    children,
  }: {
    dataKey: string;
    fill: string;
    children?: React.ReactNode;
  }) => (
    <div data-testid="bar" data-vendor={dataKey} data-fill={fill}>
      {children}
    </div>
  ),
  LabelList: () => <div data-testid="label-list" />,
  CartesianGrid: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  Legend: () => null,
}));

function makeChart(overrides: Partial<BgeChart> = {}): BgeChart {
  return {
    vendors: ["TELUS", "Rogers"],
    total_millions: 30,
    data: [
      { bge_code: "A", organization_name: "Org A", TELUS: 10, Rogers: 5 },
      { bge_code: "B", organization_name: "Org B", TELUS: 8, Rogers: 7 },
    ],
    ...overrides,
  };
}

describe("SpendByBge", () => {
  it("renders the heading", () => {
    render(<SpendByBge chart={makeChart()} />);
    expect(screen.getByRole("heading", { name: "Spend by BGE" })).toBeInTheDocument();
  });

  it("renders the loading state", () => {
    render(<SpendByBge isLoading />);
    expect(screen.getByText("Loading BGE chart…")).toBeInTheDocument();
    expect(screen.queryByTestId("barchart")).not.toBeInTheDocument();
  });

  it("renders the error state when the query failed", () => {
    render(<SpendByBge isError />);
    expect(screen.getByText("Unable to load BGE data.")).toBeInTheDocument();
  });

  it("lists a row per BGE with vendor spend and a total on the Table tab", async () => {
    const user = userEvent.setup();
    render(<SpendByBge chart={makeChart()} />);

    await user.click(screen.getByRole("tab", { name: "Table" }));

    const row = screen.getByRole("row", { name: /Org A/ });
    expect(within(row).getByText("$10.0M")).toBeInTheDocument();
    expect(within(row).getByText("$5.0M")).toBeInTheDocument();
    expect(within(row).getByText("$15.0M")).toBeInTheDocument();
  });

  it("leaves zero-spend rows out of the table too", async () => {
    const user = userEvent.setup();
    const chart = makeChart({
      data: [
        { bge_code: "A", organization_name: "Org A", TELUS: 10, Rogers: 5 },
        { bge_code: "Z", organization_name: "Org Z", TELUS: 0, Rogers: 0 },
      ],
    });
    render(<SpendByBge chart={chart} />);

    await user.click(screen.getByRole("tab", { name: "Table" }));

    expect(screen.getByRole("row", { name: /Org A/ })).toBeInTheDocument();
    expect(screen.queryByRole("row", { name: /Org Z/ })).not.toBeInTheDocument();
  });

  it("always renders the subtitle and, when given, the date range label", () => {
    render(<SpendByBge chart={makeChart()} dateRangeLabel="FY2024 Q1" />);

    expect(
      screen.getByText(
        "The chart shows the breakdown of how much each BGE spends with TELUS and Rogers.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("FY2024 Q1")).toBeInTheDocument();
  });

  it("omits the date range label when not provided", () => {
    render(<SpendByBge chart={makeChart()} />);
    expect(screen.queryByText("FY2024 Q1")).not.toBeInTheDocument();
  });

  it("shows the empty state when every row has a zero total", () => {
    const chart = makeChart({
      data: [{ bge_code: "A", organization_name: "Org A", TELUS: 0, Rogers: 0 }],
    });
    render(<SpendByBge chart={chart} />);

    expect(screen.getByText("No data for this period.")).toBeInTheDocument();
    expect(screen.queryByTestId("barchart")).not.toBeInTheDocument();
  });

  it("filters out rows whose vendor totals sum to zero", () => {
    const chart = makeChart({
      data: [
        { bge_code: "A", organization_name: "Org A", TELUS: 10, Rogers: 5 },
        { bge_code: "Z", organization_name: "Org Z", TELUS: 0, Rogers: 0 },
      ],
    });
    render(<SpendByBge chart={chart} />);

    const barChart = screen.getByTestId("barchart");
    expect(barChart).toHaveAttribute("data-rows", "1");
    expect(barChart).toHaveAttribute("data-codes", "A");
  });

  it("renders one bar per vendor coloured from VENDOR_COLOURS", () => {
    render(<SpendByBge chart={makeChart()} />);

    const bars = screen.getAllByTestId("bar");
    expect(bars.map((b) => b.getAttribute("data-vendor"))).toEqual([
      "TELUS",
      "Rogers",
    ]);
    expect(bars[0]).toHaveAttribute("data-fill", VENDOR_COLOURS.TELUS);
    expect(bars[1]).toHaveAttribute("data-fill", VENDOR_COLOURS.Rogers);
  });

  it("falls back to a default colour for an unknown vendor", () => {
    const chart = makeChart({
      vendors: ["Mystery"],
      data: [{ bge_code: "A", organization_name: "Org A", Mystery: 4 }],
    });
    render(<SpendByBge chart={chart} />);

    expect(screen.getByTestId("bar")).toHaveAttribute("data-fill", "#aaaaaa");
  });

  it("renders the total label on the last vendor's bar only", () => {
    render(<SpendByBge chart={makeChart()} />);

    const labels = screen.getAllByTestId("label-list");
    expect(labels).toHaveLength(1);

    const lastBar = screen.getByText(
      (_, el) => el?.getAttribute("data-vendor") === "Rogers",
    );
    expect(lastBar.querySelector('[data-testid="label-list"]')).not.toBeNull();
  });
});
