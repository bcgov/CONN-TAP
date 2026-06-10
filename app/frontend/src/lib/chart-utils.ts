import type { Data, Layout } from "plotly.js";

export type PlotlyTrace = { name?: string; text?: string[]; x?: unknown[] };

export type PlotlyChart = {
  data: Data[];
  layout: Partial<Layout>;
};

export const isPlotlyChart = (chart: unknown): chart is PlotlyChart =>
  Boolean(
    chart &&
      typeof chart === "object" &&
      "data" in chart &&
      "layout" in chart &&
      Array.isArray((chart as PlotlyChart).data)
  );

export type IndicatorItem = {
  label: string;
  value_millions: number;
};

export type IndicatorChart = {
  indicators: IndicatorItem[];
};

export const isIndicatorChart = (chart: unknown): chart is IndicatorChart =>
  Boolean(
    chart &&
      typeof chart === "object" &&
      "indicators" in chart &&
      Array.isArray((chart as IndicatorChart).indicators)
  );

export type TimelinePoint = {
  period: string;
  label: string;
  value: number;
};

export type TimelineChart = {
  data: TimelinePoint[];
  valueLabel: string;
};

export const isTimelineChart = (chart: unknown): chart is TimelineChart =>
  Boolean(
    chart &&
      typeof chart === "object" &&
      "data" in chart &&
      Array.isArray((chart as TimelineChart).data)
  );

export type SectorSlice = {
  sector: string;
  spend_millions: number;
  percentage: number;
  fill: string;
};

export type SectorChart = {
  data: SectorSlice[];
  total_millions: number;
  dataKey: "spend_millions";
  nameKey: "sector";
};

export const isSectorChart = (chart: unknown): chart is SectorChart =>
  Boolean(
    chart &&
      typeof chart === "object" &&
      "data" in chart &&
      "total_millions" in chart &&
      Array.isArray((chart as SectorChart).data)
  );

export type BgeBarEntry = {
  organization_name: string;
  [key: string]: string | number;
};

export type BgeChart = {
  data: BgeBarEntry[];
  vendors: string[];
  total_millions: number;
};

export const isBgeChart = (chart: unknown): chart is BgeChart =>
  Boolean(
    chart &&
      typeof chart === "object" &&
      "data" in chart &&
      "vendors" in chart &&
      Array.isArray((chart as BgeChart).data)
  );

export const VENDOR_COLOURS: Record<string, string> = {
  TELUS: "var(--color-vendor-telus)",
  Rogers: "var(--color-vendor-rogers)",
};

export const applyOutsideLabels = (traces: Data[], activeProviders: Set<string>): Data[] => {
  const active = traces.filter((t) => activeProviders.has((t as PlotlyTrace).name ?? ""));
  return active.map((trace, idx) => {
    if (idx < active.length - 1) return { ...trace, textposition: "none" };
    const len = (trace as PlotlyTrace).x?.length ?? 0;
    const combined = Array.from({ length: len }, (_, i) =>
      [...active]
        .reverse()
        .map((t) => ((t as PlotlyTrace).text ?? [])[i] ?? "")
        .filter(Boolean)
        .join("<br>")
    );
    return { ...trace, text: combined, textposition: "outside" };
  });
};
