import type { Data, Layout } from "plotly.js";

export type PlotlyTrace = {
  name?: string;
  text?: string[];
  x?: unknown[];
  y?: unknown[];
};

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

// Giving separate display names for some sectors to allow better customization
const SECTOR_DISPLAY_NAMES: Record<string, string> = {
  "Gov & ECC": "Gov BC",
  "Health Authorities": "Health",
  "Crown Corporations": "Crown Corp",
};

export const displaySector = (sector: string) =>
  SECTOR_DISPLAY_NAMES[sector] ?? sector;

export const isSectorChart = (chart: unknown): chart is SectorChart =>
  Boolean(
    chart &&
      typeof chart === "object" &&
      "data" in chart &&
      "total_millions" in chart &&
      Array.isArray((chart as SectorChart).data)
  );

export type BgeBarEntry = {
  bge_code: string;
  organization_name: string;
  [key: string]: string | number;
};

export type BgeChart = {
  data: BgeBarEntry[];
  vendors: string[];
  total_millions: number;
};

export type BgeRow = BgeBarEntry & { _total: number };

/**
 * Rows that actually have spend, with their vendor totals summed. Shared by the
 * BGE graph and table so both show the same set.
 */
export const bgeRowsWithTotals = (chart: BgeChart): BgeRow[] =>
  chart.data
    .map((entry) => ({
      ...entry,
      _total: chart.vendors.reduce(
        (sum, vendor) => sum + ((entry[vendor] as number) ?? 0),
        0,
      ),
    }))
    .filter((entry) => entry._total > 0);

export const isBgeChart = (chart: unknown): chart is BgeChart =>
  Boolean(
    chart &&
      typeof chart === "object" &&
      "data" in chart &&
      "vendors" in chart &&
      Array.isArray((chart as BgeChart).data)
  );

export type SummaryCategory = {
  code: string;
  name: string;
};

export type SummaryRow = {
  id: string;
  parent_id: string | null;
  name: string;
  type: string; // "BGE" | "Sub Org" | "Service Designee"
  level: number; // 0 | 1 | 2
  values: Record<string, number>;
  total: number;
};

export type SummaryTable = {
  categories: SummaryCategory[];
  providers: string[];
  rows: SummaryRow[];
  total_millions: number;
};

export const isSummaryTable = (table: unknown): table is SummaryTable =>
  Boolean(
    table &&
      typeof table === "object" &&
      "categories" in table &&
      "rows" in table &&
      Array.isArray((table as SummaryTable).rows) &&
      Array.isArray((table as SummaryTable).categories)
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

export type CategoryRow = {
  category: string;
  total: number;
  [provider: string]: string | number;
};

/**
 * Flattens the service-category Plotly traces (one per provider, each with the
 * categories on x and spend on y) into a row per category for the table view.
 */
export const plotlyCategoryRows = (
  chart: PlotlyChart,
): { providers: string[]; rows: CategoryRow[] } => {
  const traces = chart.data as PlotlyTrace[];
  const providers = traces.map((trace) => trace.name ?? "");

  const categories: string[] = [];
  for (const trace of traces) {
    for (const value of trace.x ?? []) {
      const category = String(value);
      if (!categories.includes(category)) categories.push(category);
    }
  }

  const rows = categories
    .map((category) => {
      const row: CategoryRow = { category, total: 0 };
      for (const trace of traces) {
        const index = (trace.x ?? []).findIndex(
          (value) => String(value) === category,
        );
        const spend = index >= 0 ? Number((trace.y ?? [])[index] ?? 0) : 0;
        row[trace.name ?? ""] = spend;
        row.total += spend;
      }
      return row;
    })
    .filter((row) => row.total > 0);

  return { providers, rows };
};
