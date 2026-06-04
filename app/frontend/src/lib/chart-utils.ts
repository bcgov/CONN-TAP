import type { Data, Layout } from "plotly.js";

export type PlotlyTrace = { name?: string; text?: string[]; x?: unknown[] };

export type PlotlyChart = {
  data: Data[];
  layout: Partial<Layout>;
};

export function isPlotlyChart(chart: unknown): chart is PlotlyChart {
  return Boolean(
    chart &&
      typeof chart === "object" &&
      "data" in chart &&
      "layout" in chart &&
      Array.isArray((chart as PlotlyChart).data)
  );
}

export function applyOutsideLabels(traces: Data[], activeProviders: Set<string>): Data[] {
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
}
