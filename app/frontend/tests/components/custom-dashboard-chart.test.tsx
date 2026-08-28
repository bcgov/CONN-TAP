import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { CustomDashboardChart } from "@/components/custom-dashboard-chart";

vi.mock("@/components/chart-download-button", () => ({
  ChartDownloadButton: ({
    title,
    label,
    formats,
  }: {
    title: string;
    label?: string;
    formats?: string[];
  }) => (
    <button
      data-testid="download-btn"
      data-title={title}
      data-label={label ?? ""}
      data-formats={formats?.join(",") ?? ""}
    >
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

  it("renders the header above the content", () => {
    render(
      <CustomDashboardChart title="Spend Chart" header={<h2>My heading</h2>}>
        chart content
      </CustomDashboardChart>,
    );

    expect(screen.getByRole("heading", { name: "My heading" })).toBeInTheDocument();
    expect(screen.getByText("chart content")).toBeInTheDocument();
  });

  it("renders no tabs when there is no table view", () => {
    render(<CustomDashboardChart title="Spend Chart">graph</CustomDashboardChart>);
    expect(screen.queryByRole("tab")).not.toBeInTheDocument();
  });

  describe("with a table view", () => {
    const renderWithTable = (props = {}) =>
      render(
        <CustomDashboardChart
          title="Spend Chart"
          header={<h2>My heading</h2>}
          table={<span>table view</span>}
          {...props}
        >
          <span>graph view</span>
        </CustomDashboardChart>,
      );

    it("shows the graph first and switches to the table", async () => {
      const user = userEvent.setup();
      renderWithTable();

      expect(screen.getByRole("tab", { name: "Graph" })).toHaveAttribute(
        "aria-selected",
        "true",
      );
      expect(screen.getByText("graph view")).toBeInTheDocument();

      await user.click(screen.getByRole("tab", { name: "Table" }));

      expect(screen.getByText("table view")).toBeInTheDocument();
      expect(screen.queryByText("graph view")).not.toBeInTheDocument();
    });

    it("keeps the header visible on both tabs", async () => {
      const user = userEvent.setup();
      renderWithTable();

      await user.click(screen.getByRole("tab", { name: "Table" }));

      expect(screen.getByRole("heading", { name: "My heading" })).toBeInTheDocument();
    });

    it("keeps the download button available on the table tab", async () => {
      const user = userEvent.setup();
      renderWithTable();

      expect(screen.getByTestId("download-btn")).toBeInTheDocument();

      await user.click(screen.getByRole("tab", { name: "Table" }));

      expect(screen.getByTestId("download-btn")).toBeInTheDocument();
    });

    it("switches to xls/csv/png/jpeg/pdf order on the table tab", async () => {
      const user = userEvent.setup();
      renderWithTable();

      // Graph tab stays image-only, even with csvData passed — an explicit
      // default (rather than leaving `formats` undefined) is what stops
      // ChartDownloadButton from adding csv/xls on its own.
      expect(screen.getByTestId("download-btn")).toHaveAttribute(
        "data-formats",
        "png,jpeg,pdf",
      );

      await user.click(screen.getByRole("tab", { name: "Table" }));

      expect(screen.getByTestId("download-btn")).toHaveAttribute(
        "data-formats",
        "xls,csv,png,jpeg,pdf",
      );
    });

    it("lets tableFormats override the table tab's default order", async () => {
      const user = userEvent.setup();
      renderWithTable({ tableFormats: ["csv", "pdf"] });

      await user.click(screen.getByRole("tab", { name: "Table" }));

      expect(screen.getByTestId("download-btn")).toHaveAttribute(
        "data-formats",
        "csv,pdf",
      );
    });

    it("points each tab at the panel it controls", () => {
      renderWithTable();

      const graphTab = screen.getByRole("tab", { name: "Graph" });
      expect(screen.getByRole("tabpanel")).toHaveAttribute(
        "id",
        graphTab.getAttribute("aria-controls"),
      );
    });
  });

  describe("state placeholders", () => {
    const renderWithState = (state: Record<string, unknown>) =>
      render(
        <CustomDashboardChart
          title="Spend Chart"
          table={<span>table view</span>}
          state={{
            isLoading: false,
            isEmpty: false,
            loadingLabel: "Loading…",
            errorLabel: "Something broke.",
            emptyLabel: "No data.",
            ...state,
          }}
        >
          <span>graph view</span>
        </CustomDashboardChart>,
      );

    it("shows the loading label instead of the view", () => {
      renderWithState({ isLoading: true });

      expect(screen.getByText("Loading…")).toBeInTheDocument();
      expect(screen.queryByText("graph view")).not.toBeInTheDocument();
    });

    it("shows the error label", () => {
      renderWithState({ isError: true });
      expect(screen.getByText("Something broke.")).toBeInTheDocument();
    });

    it("shows the empty label", () => {
      renderWithState({ isEmpty: true });
      expect(screen.getByText("No data.")).toBeInTheDocument();
    });

    it("replaces the table view too", async () => {
      const user = userEvent.setup();
      renderWithState({ isEmpty: true });

      await user.click(screen.getByRole("tab", { name: "Table" }));

      expect(screen.getByText("No data.")).toBeInTheDocument();
      expect(screen.queryByText("table view")).not.toBeInTheDocument();
    });

    it("shows the view when there is data", () => {
      renderWithState({});
      expect(screen.getByText("graph view")).toBeInTheDocument();
    });
  });
});
