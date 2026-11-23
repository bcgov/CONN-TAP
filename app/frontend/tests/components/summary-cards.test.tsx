import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FilterPanel } from "@/components/filter-panel";
import { ReportingStatus } from "@/components/reporting-status";
import { SpendBreakdown } from "@/components/spend-breakdown";
import { SpendIndicatorCards } from "@/components/spend-indicator-cards";
import { SummaryStat } from "@/components/summary-stat";

describe("SpendBreakdown", () => {
  const items = [
    { label: "TELUS", valueMillions: 4.4, percentage: 62.86, colour: "purple" },
    { label: "Rogers", valueMillions: 2.6, percentage: 37.14, colour: "red" },
  ];

  it("shows the total, each provider's amount and share, and the bar", () => {
    render(<SpendBreakdown totalMillions={7} items={items} />);

    expect(screen.getByText("$7M")).toBeInTheDocument();
    expect(screen.getByText("$4.4M")).toBeInTheDocument();
    expect(screen.getByText("63%")).toBeInTheDocument();
    expect(screen.getByText("37%")).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "TELUS 63 percent; Rogers 37 percent" }),
    ).toBeInTheDocument();
  });

  it("shows a dash while loading", () => {
    render(<SpendBreakdown isLoading totalMillions={0} items={[]} />);

    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});

describe("SummaryStat", () => {
  it("shows the label, value and detail", () => {
    render(<SummaryStat label="Peak Month" value="Jun 2026" detail="$9.1M" />);

    expect(screen.getByText("Peak Month")).toBeInTheDocument();
    expect(screen.getByText("Jun 2026")).toBeInTheDocument();
    expect(screen.getByText("$9.1M")).toBeInTheDocument();
  });

  it("leaves out the detail line when there is none", () => {
    const { container } = render(<SummaryStat label="Peak Month" value="—" />);

    expect(container.querySelectorAll("p")).toHaveLength(2);
  });
});

describe("ReportingStatus", () => {
  it("shows the title", () => {
    render(<ReportingStatus />);

    expect(screen.getByText("Reporting Status")).toBeInTheDocument();
  });
});

describe("FilterPanel", () => {
  it("shows the title, the header buttons and its content", () => {
    render(
      <FilterPanel>
        <p>Some filter</p>
      </FilterPanel>,
    );

    expect(screen.getByRole("complementary", { name: "Filters" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset all" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Close filters" })).toBeInTheDocument();
    expect(screen.getByText("Some filter")).toBeInTheDocument();
  });
});

describe("SpendIndicatorCards", () => {
  it("shows each indicator with its amount", () => {
    render(
      <SpendIndicatorCards
        indicators={[{ label: "Total TELUS Spend", value_millions: 7.98, provider: "TELUS" }]}
      />,
    );

    expect(screen.getByText("Total TELUS Spend")).toBeInTheDocument();
    expect(screen.getByText("$7.98M")).toBeInTheDocument();
  });

  it("shows loading cards while loading", () => {
    render(<SpendIndicatorCards indicators={[]} isLoading />);

    expect(screen.getAllByText("Loading…")).toHaveLength(3);
  });
});
