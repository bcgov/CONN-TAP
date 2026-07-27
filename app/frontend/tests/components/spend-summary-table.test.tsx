import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { SummaryTable } from "@/lib/chart-utils";
import { SpendSummaryTable } from "@/components/spend-summary-table";

// A two-category table with a BGE parent, a Sub Org child, and a Service
// Designee grandchild so the nested parent_id -> tree logic gets exercised.
function makeTable(): SummaryTable {
  return {
    total_millions: 30,
    categories: [
      { code: "voice", name: "Voice" },
      { code: "data", name: "Data" },
    ],
    rows: [
      {
        id: "bge-1",
        parent_id: null,
        name: "Ministry of Health",
        type: "BGE",
        level: 0,
        values: { voice: 10, data: 8 },
        total: 18,
      },
      {
        id: "sub-1",
        parent_id: "bge-1",
        name: "Health IT",
        type: "Sub Org",
        level: 1,
        values: { voice: 6, data: 5 },
        total: 11,
      },
      {
        id: "sd-1",
        parent_id: "sub-1",
        name: "Vendor A",
        type: "Service Designee",
        level: 2,
        values: { voice: 2, data: 1 },
        total: 3,
      },
      {
        id: "bge-2",
        parent_id: null,
        name: "Ministry of Education",
        type: "BGE",
        level: 0,
        values: { voice: 7, data: 5 },
        total: 12,
      },
    ],
  };
}

describe("SpendSummaryTable", () => {
  it("renders the empty state when there are no rows", () => {
    const table = { ...makeTable(), rows: [] };
    render(<SpendSummaryTable table={table} />);

    expect(screen.getByText("No data for this period.")).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("renders the date range label when provided", () => {
    render(<SpendSummaryTable table={makeTable()} dateRangeLabel="FY2024 Q1" />);
    expect(screen.getByText("FY2024 Q1")).toBeInTheDocument();
  });

  it("does not render a date range label when omitted", () => {
    render(<SpendSummaryTable table={makeTable()} />);
    expect(screen.queryByText(/FY\d{4}/)).not.toBeInTheDocument();
  });

  it("renders the fixed and category column headers", () => {
    render(<SpendSummaryTable table={makeTable()} />);

    expect(screen.getByText("BGE/Sub-org/SD")).toBeInTheDocument();
    expect(screen.getByText("Type")).toBeInTheDocument();
    expect(screen.getByText("Voice")).toBeInTheDocument();
    expect(screen.getByText("Data")).toBeInTheDocument();
    expect(screen.getByText("Total Spend")).toBeInTheDocument();
  });

  it("shows only the top-level (root) rows before expansion", () => {
    render(<SpendSummaryTable table={makeTable()} />);

    expect(screen.getByText("Ministry of Health")).toBeInTheDocument();
    expect(screen.getByText("Ministry of Education")).toBeInTheDocument();
    // Children are collapsed until their parent is expanded.
    expect(screen.queryByText("Health IT")).not.toBeInTheDocument();
    expect(screen.queryByText("Vendor A")).not.toBeInTheDocument();
  });

  it("formats spend values as rounded millions", () => {
    render(<SpendSummaryTable table={makeTable()} />);

    const healthRow = screen.getByText("Ministry of Health").closest("tr")!;
    const cells = within(healthRow);
    expect(cells.getByText("$10M")).toBeInTheDocument();
    expect(cells.getByText("$8M")).toBeInTheDocument();
    expect(cells.getByText("$18M")).toBeInTheDocument();
  });

  it("reveals nested child rows when a parent is expanded", async () => {
    const user = userEvent.setup();
    render(<SpendSummaryTable table={makeTable()} />);

    const healthRow = screen.getByText("Ministry of Health").closest("tr")!;
    await user.click(within(healthRow).getByRole("button", { name: /expand/i }));

    expect(screen.getByText("Health IT")).toBeInTheDocument();
    // The grandchild stays hidden until its own parent is expanded.
    expect(screen.queryByText("Vendor A")).not.toBeInTheDocument();
  });

  it("drills all the way down to the Service Designee grandchild", async () => {
    const user = userEvent.setup();
    render(<SpendSummaryTable table={makeTable()} />);

    const healthRow = screen.getByText("Ministry of Health").closest("tr")!;
    await user.click(within(healthRow).getByRole("button", { name: /expand/i }));

    const subRow = screen.getByText("Health IT").closest("tr")!;
    await user.click(within(subRow).getByRole("button", { name: /expand/i }));

    const vendorRow = screen.getByText("Vendor A").closest("tr")!;
    const cells = within(vendorRow);
    expect(cells.getByText("Service Designee")).toBeInTheDocument();
    expect(cells.getByText("$2M")).toBeInTheDocument();
    expect(cells.getByText("$1M")).toBeInTheDocument();
    expect(cells.getByText("$3M")).toBeInTheDocument();
  });

  it("labels expandable roll-up rows as <type>/Total and leaves the base type on leaves", () => {
    render(<SpendSummaryTable table={makeTable()} />);

    // Health has a Sub Org child, so its BGE row is a roll-up total.
    const healthRow = screen.getByText("Ministry of Health").closest("tr")!;
    expect(within(healthRow).getByText("BGE/Total")).toBeInTheDocument();

    // Education has no children, so it keeps the plain base type.
    const eduRow = screen.getByText("Ministry of Education").closest("tr")!;
    expect(within(eduRow).getByText("BGE")).toBeInTheDocument();
  });

  it("hides children again when the parent toggle is clicked twice", async () => {
    const user = userEvent.setup();
    render(<SpendSummaryTable table={makeTable()} />);

    const healthRow = screen.getByText("Ministry of Health").closest("tr")!;
    const toggle = () =>
      user.click(
        within(healthRow).getByRole("button", { name: /expand|collapse/i }),
      );

    await toggle();
    expect(screen.getByText("Health IT")).toBeInTheDocument();

    await toggle();
    expect(screen.queryByText("Health IT")).not.toBeInTheDocument();
  });

  it("shows sub-$1M spend as whole dollars rather than $0M", () => {
    const table: SummaryTable = {
      ...makeTable(),
      rows: [
        {
          id: "bge-1",
          parent_id: null,
          name: "Small Ministry",
          type: "BGE",
          level: 0,
          values: { voice: 0.08, data: 0.42 },
          total: 0.5,
        },
      ],
    };
    render(<SpendSummaryTable table={table} />);

    const row = screen.getByText("Small Ministry").closest("tr")!;
    expect(within(row).getByText("$80,000")).toBeInTheDocument();
    expect(within(row).getByText("$420,000")).toBeInTheDocument();
    expect(within(row).getByText("$500,000")).toBeInTheDocument();
    expect(within(row).queryByText("$0M")).not.toBeInTheDocument();
  });
});
