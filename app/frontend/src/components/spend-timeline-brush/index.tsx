"use client";

import { useRef, useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { type TimelineChart, type TimelinePoint } from "@/lib/chart-utils";
import { formatMonthLabel } from "@/lib/date-utils";
import type { MouseHandlerDataParam } from "recharts/types/synchronisation/types";
import styles from "./spend-timeline-brush.module.css";

interface Props {
  chart: TimelineChart | null;
  isLoading: boolean;
  onPeriodsChange: (periods: string[]) => void;
  yAxisFormatter?: (v: number) => string;
  tooltipFormatter?: (v: number) => string;
}

type DisplayPoint = TimelinePoint & { base_value: number | null; selected_value: number | null };

/** Months pre-selected on first load — the most recent rolling year. */
const DEFAULT_WINDOW = 12;

/** Months that fit the visible frame; anything older scrolls in from the left. */
const MONTHS_IN_FRAME = 48;

/** Chart margins that bracket the plot area — the year bands line up with them. */
const PLOT_MARGIN = { top: 8, right: 24, bottom: 4, left: 8 };
const Y_AXIS_WIDTH = 52;

/** One entry per run of consecutive months in the same year, for the year band. */
const toYearSpans = (points: TimelinePoint[]) =>
  points.reduce<{ year: string; months: number }[]>((spans, point) => {
    const year = point.period.slice(0, 4);
    const current = spans[spans.length - 1];
    if (current?.year === year) current.months += 1;
    else spans.push({ year, months: 1 });
    return spans;
  }, []);

export const SpendTimelineBrush = ({
  chart,
  isLoading,
  onPeriodsChange,
  yAxisFormatter = (v) => String(Number(v).toFixed(0)),
  tooltipFormatter = (v) => String(Number(v).toFixed(1)),
}: Props) => {
  const initialized = useRef(false);
  const scrollerRef = useRef<HTMLDivElement>(null);
  const points = chart?.data ?? [];

  const [selection, setSelection] = useState<{ start: string; end: string } | null>(null);
  const [drag, setDrag] = useState<{ start: string; end: string } | null>(null);

  useEffect(() => {
    initialized.current = false;
    setSelection(null);
    setDrag(null);
  }, [chart]);

  useEffect(() => {
    if (!points.length || initialized.current) return;
    initialized.current = true;
    const start = Math.max(0, points.length - DEFAULT_WINDOW);
    const end = points.length - 1;
    setSelection({ start: points[start].label, end: points[end].label });
    onPeriodsChange(points.slice(start, end + 1).map((p) => p.period));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points]);

  // Open on the most recent months — the older ones scroll in from the left.
  useEffect(() => {
    const scroller = scrollerRef.current;
    if (scroller) scroller.scrollLeft = scroller.scrollWidth;
  }, [points.length]);

  const getRange = (startLabel: string, endLabel: string): [number, number] => {
    const a = points.findIndex((p) => p.label === startLabel);
    const b = points.findIndex((p) => p.label === endLabel);
    return a <= b ? [a, b] : [b, a];
  };

  const periodsForLabels = (startLabel: string, endLabel: string): string[] => {
    const [lo, hi] = getRange(startLabel, endLabel);
    if (lo < 0 || hi < 0) return [];
    return points.slice(lo, hi + 1).map((p) => p.period);
  };

  const handleMouseDown = (e: MouseHandlerDataParam) => {
    const label = String(e?.activeLabel ?? "");
    if (!label) return;
    setDrag({ start: label, end: label });
  };

  const handleMouseMove = (e: MouseHandlerDataParam) => {
    if (!drag) return;
    const label = String(e?.activeLabel ?? "");
    if (!label) return;
    setDrag((prev) => prev && { ...prev, end: label });
  };

  const handleMouseUp = () => {
    if (!drag) return;
    const periods = periodsForLabels(drag.start, drag.end);
    if (periods.length > 0) {
      const [lo, hi] = getRange(drag.start, drag.end);
      setSelection({ start: points[lo].label, end: points[hi].label });
      onPeriodsChange(periods);
    }
    setDrag(null);
  };

  const visible = drag ?? selection;

  const [lo, hi] = visible ? getRange(visible.start, visible.end) : [-1, -1];
  const displayData: DisplayPoint[] = points.map((p, i) => ({
    ...p,
    base_value: visible && i > lo && i < hi ? null : p.value,
    selected_value: visible && i >= lo && i <= hi ? p.value : null,
  }));

  const selStartLabel = visible?.start ?? "";
  const selEndLabel = visible?.end ?? "";
  const valueLabel = chart?.valueLabel ?? "Value";

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.title}>Filter by period</span>
          {selStartLabel && selEndLabel && (
            <span className={styles.range}>
              {selStartLabel === selEndLabel
                ? selStartLabel
                : `${selStartLabel} – ${selEndLabel}`}
            </span>
          )}
        </div>
        <span className={styles.hint}>drag to select a range</span>
      </div>
      {isLoading ? (
        <p className="dashboard-card__empty">Loading timeline...</p>
      ) : (
        <div className={styles.scroller} ref={scrollerRef}>
          <div
            className={styles.chart}
            style={{ width: `${Math.max(100, (points.length / MONTHS_IN_FRAME) * 100)}%` }}
            onMouseLeave={handleMouseUp}
          >
            <ResponsiveContainer width="100%" height={160}>
              <LineChart
                data={displayData}
                margin={PLOT_MARGIN}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8e8e8" />
                <XAxis
                  dataKey="label"
                  tickFormatter={(_, index) =>
                    formatMonthLabel(points[index]?.period ?? "")
                  }
                  tick={{ fontSize: 10, fill: "#474543" }}
                  interval={0}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tickFormatter={yAxisFormatter}
                  width={Y_AXIS_WIDTH}
                  tick={{ fontSize: 11, fill: "#474543" }}
                  axisLine={false}
                  tickLine={false}
                />
                {!drag && (
                  <Tooltip
                    formatter={(value) => [tooltipFormatter(Number(value)), valueLabel]}
                    contentStyle={{ fontSize: 12 }}
                  />
                )}
                <Line
                  type="monotone"
                  dataKey="base_value"
                  stroke="#b0bec5"
                  strokeWidth={1.5}
                  dot={false}
                  activeDot={false}
                  name={valueLabel}
                  isAnimationActive={false}
                  legendType="none"
                />
                <Line
                  type="monotone"
                  dataKey="selected_value"
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
            <div
              className={styles.yearAxis}
              style={{
                paddingLeft: PLOT_MARGIN.left + Y_AXIS_WIDTH,
                paddingRight: PLOT_MARGIN.right,
              }}
              aria-hidden="true"
            >
              {toYearSpans(points).map((span) => (
                <span
                  key={span.year}
                  className={styles.yearBand}
                  style={{ flexGrow: span.months }}
                >
                  {span.year}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
