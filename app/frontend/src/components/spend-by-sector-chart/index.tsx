"use client";

import type { SectorChart } from "@/lib/chart-utils";
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
import styles from "./spend-by-sector-chart.module.css";


type Props = {
  chart: SectorChart;
  dateRangeLabel?: string;
  isLoading?: boolean;
};

export const SpendBySectorChart = ({ chart, dateRangeLabel, isLoading }: Props) => {
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
              innerRadius={60}
              outerRadius={110}
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
                String(sector),
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
                          {entry.value ?? ""} = {slice?.percentage ?? 0}% ({fmtMillions(slice?.spend_millions ?? 0)})
                        </li>
                      );
                    })}
                  </ul>
                ) : null
              }
            />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
