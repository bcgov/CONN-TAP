import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CustomDashboardChart } from "@/components/custom-dashboard-chart";

vi.mock("@/components/chart-download-button", () => ({
  ChartDownloadButton: ({ title, label }: { title: string; label?: string }) => (
    <button data-testid="download-btn" data-title={title} data-label={label ?? ""}>
      {label ?? "Download chart"}
    </button>
  ),
}));

describe("CustomDashboardChart", () => {
  it("renders children", () => {
    render(
      <CustomDashboardChart title="My Chart">
        <span>chart content</span>
      </CustomDashboardChart>,
    );
    expect(screen.getByText("chart content")).toBeInTheDocument();
  });

  it("passes title to ChartDownloadButton", () => {
    render(<CustomDashboardChart title="Spend Chart">children</CustomDashboardChart>);
    expect(screen.getByTestId("download-btn")).toHaveAttribute("data-title", "Spend Chart");
  });

  it("passes label to ChartDownloadButton when provided", () => {
    render(
      <CustomDashboardChart title="Spend Chart" label="Download">
        children
      </CustomDashboardChart>,
    );
    expect(screen.getByTestId("download-btn")).toHaveAttribute("data-label", "Download");
  });

  it("omits label when not provided", () => {
    render(<CustomDashboardChart title="Spend Chart">child</CustomDashboardChart>);
    expect(screen.getByTestId("download-btn")).toHaveAttribute("data-label", "");
  });
});
