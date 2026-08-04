import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { MRT_ColumnDef } from "material-react-table";

import { ChartDataTable } from "@/components/chart-data-table";

type Row = { name: string; spend: number };

const columns: MRT_ColumnDef<Row>[] = [
  { accessorKey: "name", header: "Name" },
  { accessorKey: "spend", header: "Spend" },
];

const data: Row[] = [
  { name: "Alpha", spend: 10 },
  { name: "Beta", spend: 20 },
];

describe("ChartDataTable", () => {
  it("renders a column per header and a row per record", () => {
    render(<ChartDataTable columns={columns} data={data} />);

    expect(screen.getByRole("columnheader", { name: "Name" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Spend" })).toBeInTheDocument();

    const row = screen.getByRole("row", { name: /Alpha/ });
    expect(within(row).getByText("10")).toBeInTheDocument();
  });

  it("shows the default empty message instead of a table when there are no rows", () => {
    render(<ChartDataTable columns={columns} data={[]} />);

    expect(screen.getByText("No data for this period.")).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("accepts a custom empty message", () => {
    render(<ChartDataTable columns={columns} data={[]} emptyLabel="Nothing here." />);
    expect(screen.getByText("Nothing here.")).toBeInTheDocument();
  });

  it("does not offer sorting", () => {
    render(<ChartDataTable columns={columns} data={data} />);

    const header = screen.getByRole("columnheader", { name: "Name" });
    expect(within(header).queryByRole("button")).not.toBeInTheDocument();
  });

  it("lets a caller override the shared MRT options", () => {
    render(
      <ChartDataTable
        columns={columns}
        data={data}
        options={{ enableSorting: true }}
      />,
    );

    const header = screen.getByRole("columnheader", { name: /Name/ });
    expect(within(header).getByRole("button")).toBeInTheDocument();
  });
});
