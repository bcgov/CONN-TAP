import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { IndicatorItem } from "@/lib/chart-utils";
import { SpendIndicatorCards } from "@/components/spend-indicator-cards";

const indicators: IndicatorItem[] = [
  { label: "Total spend", value_millions: 42.5 },
  { label: "TELUS", value_millions: 30 },
];

describe("SpendIndicatorCards", () => {
  it("renders a card per indicator with a formatted value", () => {
    render(<SpendIndicatorCards indicators={indicators} />);

    expect(screen.getByText("Total spend")).toBeInTheDocument();
    expect(screen.getByText("$42.5M")).toBeInTheDocument();
    expect(screen.getByText("TELUS")).toBeInTheDocument();
    expect(screen.getByText("$30.0M")).toBeInTheDocument();
  });

  it("renders three placeholder cards while loading and no real data", () => {
    render(<SpendIndicatorCards indicators={indicators} isLoading />);

    expect(screen.getAllByText("Loading…")).toHaveLength(3);
    expect(screen.queryByText("Total spend")).not.toBeInTheDocument();
  });

  it("renders the date range label when provided", () => {
    render(<SpendIndicatorCards indicators={indicators} dateRangeLabel="FY2024 Q1" />);
    expect(screen.getByText("FY2024 Q1")).toBeInTheDocument();
  });

  it("omits the date range label when not provided", () => {
    render(<SpendIndicatorCards indicators={indicators} />);
    expect(screen.queryByText("FY2024 Q1")).not.toBeInTheDocument();
  });
});
