"use client";

import { useRef, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchDataset } from "@/lib/dataset-api";
import { isTimelineChart, type TimelinePoint } from "@/lib/chart-utils";
import type { MouseHandlerDataParam } from "recharts/types/synchronisation/types";
import type { YearType } from "@/lib/date-utils";
import styles from "./spend-timeline-brush.module.css";

interface Props {
  yearType: YearType;
  onPeriodsChange: (periods: string[]) => void;
}

type DisplayPoint = TimelinePoint & { base_spend: number | null; selected_spend: number | null };

export function SpendTimelineBrush({ yearType, onPeriodsChange }: Props) {
  const initialized = useRef(false);

  const [selection, setSelection] = useState<{ start: string; end: string } | null>(null);
  const [drag, setDrag] = useState<{ start: string; end: string } | null>(null);

  const { data: points = [], isLoading } = useQuery({
    queryKey: ["total-spend-over-time", yearType],
    queryFn: async () => {
      const result = await fetchDataset("total-spend-over-time", yearType, [], []);
      const chart = result.metadata.chart;
      const all = isTimelineChart(chart) ? chart.data : ([] as TimelinePoint[]);
      return all.filter((p) => parseInt(p.period.split("_")[0]) >= 2024);
    },
  });

  useEffect(() => {
    initialized.current = false;
    setSelection(null);
    setDrag(null);
  }, [yearType]);

  useEffect(() => {
    if (!points.length || initialized.current) return;
    initialized.current = true;
    const start = Math.max(0, points.length - 4);
    const end = points.length - 1;
    setSelection({ start: points[start].label, end: points[end].label });
    onPeriodsChange(points.slice(start, end + 1).map((p) => p.period));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points]);

  function getRange(startLabel: string, endLabel: string): [number, number] {
    const a = points.findIndex((p) => p.label === startLabel);
    const b = points.findIndex((p) => p.label === endLabel);
    return a <= b ? [a, b] : [b, a];
  }

  function periodsForLabels(startLabel: string, endLabel: string): string[] {
    const [lo, hi] = getRange(startLabel, endLabel);
    if (lo < 0 || hi < 0) return [];
    return points.slice(lo, hi + 1).map((p) => p.period);
  }

  function handleMouseDown(e: MouseHandlerDataParam) {
    const label = String(e?.activeLabel ?? "");
    if (!label) return;
    setDrag({ start: label, end: label });
  }

  function handleMouseMove(e: MouseHandlerDataParam) {
    if (!drag) return;
    const label = String(e?.activeLabel ?? "");
    if (!label) return;
    setDrag((prev) => prev && { ...prev, end: label });
  }

  function handleMouseUp() {
    if (!drag) return;
    const periods = periodsForLabels(drag.start, drag.end);
    if (periods.length > 0) {
      const [lo, hi] = getRange(drag.start, drag.end);
      setSelection({ start: points[lo].label, end: points[hi].label });
      onPeriodsChange(periods);
    }
    setDrag(null);
  }

  const visible = drag ?? selection;

  const [lo, hi] = visible ? getRange(visible.start, visible.end) : [-1, -1];
  const displayData: DisplayPoint[] = points.map((p, i) => ({
    ...p,
    // Base line: null for interior of selection so the two lines never overlap
    base_spend: visible && i > lo && i < hi ? null : p.total_spend_millions,
    // Highlight line: full selected segment (shares boundary points with base)
    selected_spend: visible && i >= lo && i <= hi ? p.total_spend_millions : null,
  }));

  const selStartLabel = visible?.start ?? "";
  const selEndLabel = visible?.end ?? "";

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.title}>Filter by period</span>
        {selStartLabel && selEndLabel && (
          <span className={styles.range}>
            {selStartLabel === selEndLabel
              ? selStartLabel
              : `${selStartLabel} – ${selEndLabel}`}
            <span className={styles.hint}> — click and drag to select a range</span>
          </span>
        )}
      </div>
      {isLoading ? (
        <p className="dashboard-card__empty">Loading timeline...</p>
      ) : (
        <div className={styles.chart} onMouseLeave={handleMouseUp}>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart
              data={displayData}
              margin={{ top: 8, right: 24, bottom: 4, left: 8 }}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8e8e8" />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fill: "#474543" }}
                interval="preserveStartEnd"
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tickFormatter={(v) => `$${Number(v).toFixed(0)}M`}
                width={52}
                tick={{ fontSize: 11, fill: "#474543" }}
                axisLine={false}
                tickLine={false}
              />
              {!drag && (
                <Tooltip
                  formatter={(value) => [`$${Number(value).toFixed(1)}M`, "Total spend"]}
                  contentStyle={{ fontSize: 12 }}
                />
              )}
              {/* Base line — unselected range only (null in selection interior) */}
              <Line
                type="monotone"
                dataKey="base_spend"
                stroke="#b0bec5"
                strokeWidth={1.5}
                dot={false}
                activeDot={false}
                name="Total Spend"
                isAnimationActive={false}
                legendType="none"
              />
              {/* Highlight line — selected segment only */}
              <Line
                type="monotone"
                dataKey="selected_spend"
                stroke="#607d8b"
                strokeWidth={2.5}
                dot={{ r: 3.5, fill: "#607d8b", strokeWidth: 0 }}
                activeDot={{ r: 5, fill: "#455a64", strokeWidth: 0 }}
                connectNulls={false}
                name="Selected"
                isAnimationActive={false}
                legendType="none"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
