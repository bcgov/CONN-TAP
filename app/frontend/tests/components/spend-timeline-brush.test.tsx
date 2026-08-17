import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { TimelineChart } from "@/lib/chart-utils";
import { SpendTimelineBrush } from "@/components/spend-timeline-brush";

// recharts needs a real layout to lay out ticks; capture the props instead and
// exercise the axis/selection logic directly.
const captured: {
  xTickFormatter?: (value: string, index: number) => string;
} = {};

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
  LineChart: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
  Line: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  YAxis: () => null,
  XAxis: (props: { tickFormatter: (value: string, index: number) => string }) => {
    captured.xTickFormatter = props.tickFormatter;
    return null;
  },
}));

// Consecutive months from Nov 2023, so the default window straddles a year boundary.
function makeChart(length = 14): TimelineChart {
  const months = Array.from({ length }, (_, i) => {
    const monthIndex = 10 + i; // 10 = Nov 2023
    const year = 2023 + Math.floor(monthIndex / 12);
    const month = (monthIndex % 12) + 1;
    return {
      period: `${year}-${String(month).padStart(2, "0")}`,
      label: `M${i}`,
      value: i,
    };
  });
  return { data: months, valueLabel: "Total Spend" };
}

describe("SpendTimelineBrush", () => {
  it("labels the x axis with month names", () => {
    render(
      <SpendTimelineBrush chart={makeChart()} isLoading={false} onPeriodsChange={vi.fn()} />,
    );

    expect(captured.xTickFormatter?.("M0", 0)).toBe("Nov");
    expect(captured.xTickFormatter?.("M2", 2)).toBe("Jan");
    expect(captured.xTickFormatter?.("M13", 13)).toBe("Dec");
  });

  it("groups the years into bands sized by their month count", () => {
    render(
      <SpendTimelineBrush chart={makeChart()} isLoading={false} onPeriodsChange={vi.fn()} />,
    );

    const bands = screen.getAllByText(/^20\d\d$/);
    expect(bands.map((b) => b.textContent)).toEqual(["2023", "2024"]);
    expect(bands.map((b) => b.style.flexGrow)).toEqual(["2", "12"]);
  });

  it("fills the frame when the data fits two years, and widens past it when it does not", () => {
    const { container, rerender } = render(
      <SpendTimelineBrush chart={makeChart()} isLoading={false} onPeriodsChange={vi.fn()} />,
    );
    // 14 months fits inside the 24-month frame.
    expect(container.querySelector<HTMLElement>("[style*='width']")?.style.width).toBe("100%");

    rerender(
      <SpendTimelineBrush
        chart={makeChart(36)}
        isLoading={false}
        onPeriodsChange={vi.fn()}
      />,
    );
    // 36 months is 1.5 frames wide, so the extra year scrolls.
    expect(container.querySelector<HTMLElement>("[style*='width']")?.style.width).toBe("150%");
  });

  it("pre-selects the most recent twelve months", () => {
    const onPeriodsChange = vi.fn();
    render(
      <SpendTimelineBrush chart={makeChart()} isLoading={false} onPeriodsChange={onPeriodsChange} />,
    );

    const periods = onPeriodsChange.mock.calls[0][0];
    expect(periods).toHaveLength(12);
    expect(periods[0]).toBe("2024-01");
    expect(periods[11]).toBe("2024-12");
  });

  it("shows the selected range in the header", () => {
    render(
      <SpendTimelineBrush chart={makeChart()} isLoading={false} onPeriodsChange={vi.fn()} />,
    );

    expect(screen.getByText("M2 – M13")).toBeInTheDocument();
  });

  it("renders no chart while loading", () => {
    render(<SpendTimelineBrush chart={null} isLoading onPeriodsChange={vi.fn()} />);

    expect(screen.getByText("Loading timeline...")).toBeInTheDocument();
    expect(screen.queryByText("2024")).not.toBeInTheDocument();
  });
});
