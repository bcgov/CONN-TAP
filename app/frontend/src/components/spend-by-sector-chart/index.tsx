"use client";

import type { SectorChart, SectorSlice } from "@/lib/chart-utils";
import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import styles from "./spend-by-sector-chart.module.css";

const SECTOR_ABBREV: Record<string, string> = {
  "Health Authorities": "Health auth",
  "Crown Corporations": "Crown corp",
  "Gov & ECC": "Gov & ECC",
  "School Districts": "School districts",
};

function abbrev(sector: string): string {
  return SECTOR_ABBREV[sector] ?? sector;
}

function fmtM(millions: number): string {
  const rounded = parseFloat(millions.toFixed(2));
  return `$${rounded % 1 === 0 ? rounded.toFixed(0) : String(rounded).replace(/\.?0+$/, "")}M`;
}

type LegendPayloadItem = {
  value: string;
  color: string;
  payload: SectorSlice;
};

type Props = {
  chart: SectorChart;
  dateRangeLabel?: string;
  isLoading?: boolean;
};

export function SpendBySectorChart({ chart, dateRangeLabel, isLoading }: Props) {
  function renderLegend(props: { payload?: LegendPayloadItem[] }) {
    const { payload } = props;
    if (!payload) return null;
    return (
      <ul className={styles.legend}>
        {payload.map((entry) => (
          <li key={entry.value} className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: entry.color }} />
            {abbrev(entry.value)} = {entry.payload.percentage}% ({fmtM(entry.payload.spend_millions)})
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div className={styles.wrapper}>
      {dateRangeLabel && <p className={styles.dateRange}>{dateRangeLabel}</p>}
      <p className={styles.subtitle}>
        The chart shows the breakdown of telecom spend by each sector.
      </p>

      {isLoading ? (
        <p className={styles.empty}>Loading chart…</p>
      ) : chart.data.length === 0 ? (
        <p className={styles.empty}>No data for this period.</p>
      ) : (
        <ResponsiveContainer width="100%" height={320}>
          <PieChart>
            <Pie
              data={chart.data}
              dataKey={chart.dataKey}
              nameKey={chart.nameKey}
              cx="50%"
              cy="50%"
              outerRadius={110}
              label={({ percentage }) => `${percentage}%`}
              labelLine={false}
            >
              {chart.data.map((slice) => (
                <Cell key={slice.sector} fill={slice.fill} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string) => [
                `${fmtM(value)} (${chart.data.find((s) => s.sector === name)?.percentage ?? 0}%)`,
                abbrev(name),
              ]}
            />
            <Legend content={renderLegend} />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
