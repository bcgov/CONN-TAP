"use client";

import { useMemo } from "react";
import type { MRT_ColumnDef } from "material-react-table";
import { ChartDataTable } from "@/components/chart-data-table";
import { CustomDashboardChart } from "@/components/custom-dashboard-chart";
import { displaySector, type SectorChart, type SectorSlice } from "@/lib/chart-utils";
import { fmtMillions } from "@/lib/format-utils";
import {
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Sector,
  Tooltip,
  type PieLabelRenderProps,
} from "recharts";
import styles from "./spend-by-sector.module.css";

const CHART_MARGIN = { top: 40, right: 24, bottom: 8, left: 24 };

type Props = {
  chart?: SectorChart | null;
  dateRangeLabel?: string;
  isLoading?: boolean;
  isError?: boolean;
};

const SectorGraph = ({ chart }: { chart: SectorChart }) => (
  <ResponsiveContainer width="100%" height={340}>
    <PieChart margin={CHART_MARGIN}>
      <Pie
        data={chart.data}
        dataKey={chart.dataKey}
        nameKey={chart.nameKey}
        cx="50%"
        cy="50%"
        innerRadius={60}
        outerRadius={100}
        label={(props: PieLabelRenderProps & { percentage?: number }) => `${props.percentage ?? 0}%`}
        labelLine={false}
        shape={(sectorProps, index) => (
          <Sector {...sectorProps} fill={chart.data[index]?.fill ?? sectorProps.fill} />
        )}
      >
      </Pie>
      <Tooltip
        formatter={(spend, sector) => [
          `${fmtMillions(Number(spend))} (${chart.data.find((s) => s.sector === String(sector))?.percentage ?? 0}%)`,
          displaySector(String(sector)),
        ]}
      />
      <Legend
        content={({ payload: sectors }) =>
          sectors ? (
            <ul className={styles.legend}>
              {sectors.map((entry) => {
                const slice = chart.data.find((s) => s.sector === entry.value);
                return (
                  <li key={entry.value} className={styles.legendItem}>
                    <span className={styles.legendDot} style={{ background: entry.color }} />
                    {displaySector(entry.value ?? "")} = {slice?.percentage ?? 0}% ({fmtMillions(slice?.spend_millions ?? 0)})
                  </li>
                );
              })}
            </ul>
          ) : null
        }
      />
    </PieChart>
  </ResponsiveContainer>
);

const SectorTable = ({ chart }: { chart: SectorChart }) => {
  const columns = useMemo<MRT_ColumnDef<SectorSlice>[]>(
    () => [
      {
        accessorKey: "sector",
        header: "Sector",
        size: 220,
        // Colour swatch matching the pie slice, so rows map back to the graph.
        Cell: ({ row }) => (
          <span className={styles.sectorCell}>
            <span
              className={styles.legendDot}
              style={{ background: row.original.fill }}
            />
            {displaySector(row.original.sector)}
          </span>
        ),
        Footer: "Total",
      },
      {
        accessorKey: "spend_millions",
        header: "Spend",
        size: 120,
        muiTableHeadCellProps: { align: "right" },
        muiTableBodyCellProps: { align: "right" },
        muiTableFooterCellProps: { align: "right" },
        Cell: ({ cell }) => fmtMillions(cell.getValue<number>()),
        Footer: () => fmtMillions(chart.total_millions),
      },
      {
        accessorKey: "percentage",
        header: "Share",
        size: 100,
        muiTableHeadCellProps: { align: "right" },
        muiTableBodyCellProps: { align: "right" },
        muiTableFooterCellProps: { align: "right" },
        Cell: ({ cell }) => `${cell.getValue<number>()}%`,
        Footer: "100%",
      },
    ],
    [chart.total_millions],
  );

  return <ChartDataTable columns={columns} data={chart.data} />;
};

export const SpendBySector = ({
  chart,
  dateRangeLabel,
  isLoading = false,
  isError,
}: Props) => (
  <article className="dashboard-card">
    <CustomDashboardChart
      title="Telecom Spend Share by Sector"
      label="Download spend by sector chart as image"
      tabsLabel="Sector spend view"
      state={{
        isLoading,
        isError,
        isEmpty: !chart || chart.data.length === 0,
        loadingLabel: "Loading chart…",
        errorLabel: "Unable to load sector data.",
        emptyLabel: "No data for this period.",
      }}
      header={
        <div className="dashboard-card__header">
          <h2>
            Telecom Spend share by Sector ($
            {chart?.total_millions?.toFixed(1) ?? "—"}M)
          </h2>
          {dateRangeLabel && (
            <p className="dashboard-card__date-range">{dateRangeLabel}</p>
          )}
          <p>The chart shows the breakdown of telecom spend by each sector.</p>
        </div>
      }
      table={
        <div className="dashboard-card__chart">
          {chart && <SectorTable chart={chart} />}
        </div>
      }
    >
      <div className="dashboard-card__chart">
        {chart && <SectorGraph chart={chart} />}
      </div>
    </CustomDashboardChart>
  </article>
);
