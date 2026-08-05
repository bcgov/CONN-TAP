"use client";

import { useMemo } from "react";
import dynamic from "next/dynamic";
import type { MRT_ColumnDef } from "material-react-table";
import { ChartDataTable } from "@/components/chart-data-table";
import { CustomDashboardChart } from "@/components/custom-dashboard-chart";
import {
  applyOutsideLabels,
  plotlyCategoryRows,
  type CategoryRow,
  type PlotlyChart,
  type PlotlyTrace,
} from "@/lib/chart-utils";
import { fmtMillions } from "@/lib/format-utils";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

type Props = {
  chart?: PlotlyChart | null;
  dateRangeLabel?: string;
  isLoading?: boolean;
  isError?: boolean;
};

const CategoryGraph = ({ chart }: { chart: PlotlyChart }) => (
  <Plot
    data={applyOutsideLabels(
      chart.data,
      new Set(chart.data.map((trace) => (trace as PlotlyTrace).name ?? "")),
    )}
    layout={{
      ...chart.layout,
      autosize: true,
      showlegend: true,
      legend: {
        ...chart.layout.legend,
        itemclick: false,
        itemdoubleclick: false,
      },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
    }}
    config={{ displayModeBar: false, responsive: true }}
    style={{ width: "100%", height: "420px" }}
    useResizeHandler
  />
);

const CategoryTable = ({
  providers,
  rows,
}: {
  providers: string[];
  rows: CategoryRow[];
}) => {
  const columns = useMemo<MRT_ColumnDef<CategoryRow>[]>(() => {
    const spendColumn = {
      size: 130,
      muiTableHeadCellProps: {
        align: "right" as const,
        sx: { whiteSpace: "normal" },
      },
      muiTableBodyCellProps: { align: "right" as const },
      Cell: ({ cell }: { cell: { getValue: () => unknown } }) =>
        fmtMillions(Number(cell.getValue() ?? 0)),
    };

    return [
      {
        accessorKey: "category",
        header: "Service category",
        size: 260,
        muiTableHeadCellProps: { sx: { whiteSpace: "normal" } },
        muiTableBodyCellProps: { sx: { whiteSpace: "normal" } },
      },
      ...providers.map<MRT_ColumnDef<CategoryRow>>((provider) => ({
        ...spendColumn,
        accessorKey: provider,
        header: provider,
      })),
      { ...spendColumn, accessorKey: "total", header: "Total" },
    ];
  }, [providers]);

  return (
    <ChartDataTable
      columns={columns}
      data={rows}
    />
  );
};

export const SpendByCategory = ({
  chart,
  dateRangeLabel,
  isLoading = false,
  isError,
}: Props) => {
  const { providers, rows } = chart
    ? plotlyCategoryRows(chart)
    : { providers: [], rows: [] };

  return (
    <article className="dashboard-card">
      <CustomDashboardChart
        title="Spend by Service Category"
        label="Download spend by service category chart as image"
        tabsLabel="Service category spend view"
        state={{
          isLoading,
          isError,
          isEmpty: !chart,
          loadingLabel: "Loading Plotly chart...",
          errorLabel: "Unable to load service category spend data.",
          emptyLabel: "No Plotly data for this period.",
        }}
        header={
          <div className="dashboard-card__header">
            <h2>Spend by service category</h2>
            {dateRangeLabel && (
              <p className="dashboard-card__date-range">{dateRangeLabel}</p>
            )}
            <p>
              The chart shows the breakdown of Telecom spend by service category
              and highlighting how much is spent with each provider.
            </p>
          </div>
        }
        table={
          <div className="dashboard-card__chart">
            <CategoryTable providers={providers} rows={rows} />
          </div>
        }
      >
        <div className="dashboard-card__chart">
          {chart && <CategoryGraph chart={chart} />}
        </div>
      </CustomDashboardChart>
    </article>
  );
};
