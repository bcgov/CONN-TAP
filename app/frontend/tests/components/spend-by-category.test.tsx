import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { PlotlyChart } from "@/lib/chart-utils";
import { SpendByCategory } from "@/components/spend-by-category";

// react-plotly.js can't render in jsdom, so the dynamic import is stubbed.
vi.mock("next/dynamic", () => ({
  default: () => () => <div data-testid="plotly-chart" />,
}));

function makeChart(): PlotlyChart {
  return {
    layout: { legend: {} },
    data: [
      { type: "bar", name: "TELUS", x: ["Voice", "Data"], y: [10, 4], text: ["a", "b"] },
      { type: "bar", name: "Rogers", x: ["Voice", "Data"], y: [2, 0], text: ["c", ""] },
    ] as PlotlyChart["data"],
  };
}

describe("SpendByCategory", () => {
  it("renders the heading and subtitle", () => {
    render(<SpendByCategory chart={makeChart()} />);

    expect(
      screen.getByRole("heading", { name: "Spend by service category" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/breakdown of Telecom spend by service category/),
    ).toBeInTheDocument();
  });

  it("renders the date range label when provided", () => {
    render(<SpendByCategory chart={makeChart()} dateRangeLabel="FY2024 Q1" />);
    expect(screen.getByText("FY2024 Q1")).toBeInTheDocument();
  });

  it("renders the plotly chart on the Graph tab", () => {
    render(<SpendByCategory chart={makeChart()} />);
    expect(screen.getByTestId("plotly-chart")).toBeInTheDocument();
  });

  it("renders the loading state", () => {
    render(<SpendByCategory isLoading />);

    expect(screen.getByText("Loading Plotly chart...")).toBeInTheDocument();
    expect(screen.queryByTestId("plotly-chart")).not.toBeInTheDocument();
  });

  it("renders the error state when the query failed", () => {
    render(<SpendByCategory isError />);
    expect(
      screen.getByText("Unable to load service category spend data."),
    ).toBeInTheDocument();
  });

  it("renders the empty state when there is no chart", () => {
    render(<SpendByCategory chart={null} />);
    expect(screen.getByText("No Plotly data for this period.")).toBeInTheDocument();
  });

  it("turns the traces into a row per category on the Table tab", async () => {
    const user = userEvent.setup();
    render(<SpendByCategory chart={makeChart()} />);

    await user.click(screen.getByRole("tab", { name: "Table" }));

    // A column per provider, plus the total.
    for (const header of ["Service category", "TELUS", "Rogers", "Total"]) {
      expect(screen.getByRole("columnheader", { name: header })).toBeInTheDocument();
    }

    const voice = screen.getByRole("row", { name: /Voice/ });
    expect(within(voice).getByText("$10M")).toBeInTheDocument();
    expect(within(voice).getByText("$2M")).toBeInTheDocument();
    expect(within(voice).getByText("$12M")).toBeInTheDocument();
  });
});
