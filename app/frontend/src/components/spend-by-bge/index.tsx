"use client";

import { useMemo } from "react";
import type { MRT_ColumnDef } from "material-react-table";
import { ChartDataTable } from "@/components/chart-data-table";
import { CustomDashboardChart } from "@/components/custom-dashboard-chart";
import {
  bgeRowsWithTotals,
  VENDOR_COLOURS,
  type BgeChart,
  type BgeRow,
} from "@/lib/chart-utils";
import { fmtMillions, fmtMillionsFixed } from "@/lib/format-utils";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Props = {
  chart?: BgeChart | null;
  dateRangeLabel?: string;
  isLoading?: boolean;
  isError?: boolean;
};

const BgeGraph = ({ chart, rows }: { chart: BgeChart; rows: BgeRow[] }) => {
  const lastVendor = chart.vendors.at(-1);

  return (
    <ResponsiveContainer width="100%" height={380}>
      <BarChart data={rows} margin={{ top: 24, right: 16, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="bge_code"
          tick={{ fontSize: 11 }}
        />
        <YAxis
          tickFormatter={(v: number) => `$${v.toFixed(0)}M`}
          tick={{ fontSize: 11 }}
          label={{
            value: "Spend ($M)",
            angle: -90,
            position: "insideLeft",
            offset: 12,
            fontSize: 11,
          }}
        />
        <Tooltip
          formatter={(value, name) => [
            `$${Number(value ?? 0).toFixed(1)}M`,
            String(name),
          ]}
        />
        <Legend />
        {chart.vendors.map((vendor) => (
          <Bar
            key={vendor}
            dataKey={vendor}
            stackId="stack"
            fill={VENDOR_COLOURS[vendor] ?? "#aaaaaa"}
            isAnimationActive={false}
          >
            {vendor === lastVendor && (
              <LabelList
                dataKey="_total"
                position="top"
                formatter={(v) => (Number(v) > 0 ? fmtMillionsFixed(Number(v)) : "")}
                style={{ fontSize: 10, fill: "#555" }}
              />
            )}
          </Bar>
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
};

const BgeTable = ({ chart, rows }: { chart: BgeChart; rows: BgeRow[] }) => {
  const columns = useMemo<MRT_ColumnDef<BgeRow>[]>(() => {
    const spendColumn = {
      size: 120,
      muiTableHeadCellProps: { align: "right" as const },
      muiTableBodyCellProps: { align: "right" as const },
      Cell: ({ cell }: { cell: { getValue: () => unknown } }) =>
        fmtMillions(Number(cell.getValue() ?? 0)),
    };

    return [
      { accessorKey: "bge_code", header: "BGE", size: 110 },
      { accessorKey: "organization_name", header: "Organization", size: 260 },
      ...chart.vendors.map<MRT_ColumnDef<BgeRow>>((vendor) => ({
        ...spendColumn,
        accessorKey: vendor,
        header: vendor,
      })),
      { ...spendColumn, accessorKey: "_total", header: "Total" },
    ];
  }, [chart.vendors]);

  return (
    <ChartDataTable
      columns={columns}
      data={rows}
    />
  );
};

export const SpendByBge = ({
  chart,
  dateRangeLabel,
  isLoading = false,
  isError,
}: Props) => {
  // Rows whose vendor spend sums to zero are dropped from both views.
  const rows = chart ? bgeRowsWithTotals(chart) : [];

  return (
    <article className="dashboard-card">
      <CustomDashboardChart
        title="Spend by BGE"
        label="Download spend by BGE chart as image"
        tabsLabel="BGE spend view"
        state={{
          isLoading,
          isError,
          isEmpty: rows.length === 0,
          loadingLabel: "Loading BGE chart…",
          errorLabel: "Unable to load BGE data.",
          emptyLabel: "No data for this period.",
        }}
        header={
          <div className="dashboard-card__header">
            <h2>Spend by BGE</h2>
            {dateRangeLabel && (
              <p className="dashboard-card__date-range">{dateRangeLabel}</p>
            )}
            <p>
              The chart shows the breakdown of how much each BGE spends with
              TELUS and Rogers.
            </p>
          </div>
        }
        table={
          <div className="dashboard-card__chart">
            {chart && <BgeTable chart={chart} rows={rows} />}
          </div>
        }
      >
        <div className="dashboard-card__chart">
          {chart && <BgeGraph chart={chart} rows={rows} />}
        </div>
      </CustomDashboardChart>
    </article>
  );
};
