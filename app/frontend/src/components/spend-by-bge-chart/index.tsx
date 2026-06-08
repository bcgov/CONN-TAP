"use client";

import { VENDOR_COLOURS } from "@/lib/chart-utils";
import type { BgeBarEntry, BgeChart } from "@/lib/chart-utils";
import { fmtMillionsFixed } from "@/lib/format-utils";
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
import styles from "./spend-by-bge-chart.module.css";

const BGE_ABBREV: Record<string, string> = {
  "Gov BC": "Gov BC",
  "BCLC": "BCLC",
  "BC Hydro": "BC Hydro",
  "WSBC": "WSBC",
  "ECC": "ECC",
  "FHA": "FHA",
  "NHA": "NHA",
  "ICBC": "ICBC",
  "PHSA": "PHSA",
  "VIHA": "VHA",
  "FNHA": "FNHA",
  "VCHA (+PHC)": "VHA+PHC",
  "School Districts": "Sch. Dist.",
  "IHA": "IHA",
};


type WithTotal = BgeBarEntry & { _total: number };

type Props = {
  chart: BgeChart;
  dateRangeLabel?: string;
};

export const SpendByBgeChart = ({ chart, dateRangeLabel }: Props) => {
  const data: WithTotal[] = chart.data
    .map((entry) => ({
      ...entry,
      _total: chart.vendors.reduce((sum, v) => sum + (((entry[v] as number) ?? 0)), 0),
    }))
    .filter((entry) => entry._total > 0);

  const lastVendor = chart.vendors.at(-1);

  return (
    <div className={styles.wrapper}>
      {dateRangeLabel && <p className={styles.dateRange}>{dateRangeLabel}</p>}
      <p className={styles.subtitle}>
        The chart shows the breakdown of how much each BGE spends with TELUS and Rogers.
      </p>

      {data.length === 0 ? (
        <p className={styles.empty}>No data for this period.</p>
      ) : (
        <ResponsiveContainer width="100%" height={380}>
          <BarChart data={data} margin={{ top: 24, right: 16, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="organization_name"
              tickFormatter={(v: string) => BGE_ABBREV[v] ?? v}
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
      )}
    </div>
  );
};
