"use client";

import { Header, Heading } from "@bcgov/design-system-react-components";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import dynamic from "next/dynamic";
import { UserCircle2 } from "lucide-react";
import type { Data, Layout } from "plotly.js";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DashboardSidebar } from "@/components/dashboard-sidebar";
import { MinimalFooter } from "@/components/minimal-footer";
import { useMemo, useState } from "react";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

type YearType = "fiscal" | "calendar";

type DatasetEnvelope = {
  metadata: {
    chart?: unknown;
  };
};

type PlotlyChart = {
  data: Data[];
  layout: Partial<Layout>;
};

type RechartsBar = {
  dataKey: "Rogers" | "Telus";
  stackId: string;
  fill: string;
  name: string;
};

type RechartsRow = {
  serviceCategory: string;
  Rogers: number;
  Telus: number;
  total: number;
};

type RechartsChart = {
  data: RechartsRow[];
  bars: RechartsBar[];
  xAxisKey: "serviceCategory";
  yAxisLabel: string;
};

function currentFiscalYear(date = new Date()) {
  return date.getMonth() >= 3 ? date.getFullYear() + 1 : date.getFullYear();
}

function buildYearOptions(yearType: YearType) {
  const currentYear = yearType === "fiscal" ? currentFiscalYear() : new Date().getFullYear();
  const endYear = Math.max(currentYear, 2027);
  const years = [];

  for (let year = 2024; year <= endYear; year += 1) {
    years.push(year);
  }

  return years;
}

function isPlotlyChart(chart: unknown): chart is PlotlyChart {
  return Boolean(
    chart &&
      typeof chart === "object" &&
      "data" in chart &&
      "layout" in chart &&
      Array.isArray((chart as PlotlyChart).data)
  );
}

function isRechartsChart(chart: unknown): chart is RechartsChart {
  return Boolean(
    chart &&
      typeof chart === "object" &&
      "data" in chart &&
      "bars" in chart &&
      Array.isArray((chart as RechartsChart).data) &&
      Array.isArray((chart as RechartsChart).bars)
  );
}

async function fetchDataset(datasetId: string, yearType: YearType, year: number, quarter: string) {
  const params = new URLSearchParams({
    year_type: yearType,
    year: String(year),
  });

  if (quarter !== "all") {
    params.set("quarter", quarter);
  }

  const response = await fetch(`/api/v1/datasets/${datasetId}/data?${params.toString()}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Dataset request failed with status ${response.status}`);
  }

  return (await response.json()) as DatasetEnvelope;
}

export function DashboardClient({ displayName }: { displayName: string }) {
  const [yearType, setYearType] = useState<YearType>("fiscal");
  const [year, setYear] = useState(currentFiscalYear());
  const [quarter, setQuarter] = useState("all");

  const yearOptions = useMemo(() => buildYearOptions(yearType), [yearType]);
  const chartQuery = useQuery({
    queryKey: ["service-category-spend", yearType, year, quarter],
    queryFn: async () => {
      const [plotly, recharts] = await Promise.all([
        fetchDataset("service-category-spend-plotly", yearType, year, quarter),
        fetchDataset("service-category-spend-recharts", yearType, year, quarter),
      ]);

      return {
        plotly: isPlotlyChart(plotly.metadata.chart) ? plotly.metadata.chart : null,
        recharts: isRechartsChart(recharts.metadata.chart) ? recharts.metadata.chart : null,
      };
    },
  });

  const yearLabel = yearType === "fiscal" ? "Fiscal year" : "Calendar year";

  return (
    <div className="dashboard-shell">
      <DashboardSidebar />

      <div className="dashboard-right">
        <Header
          title="Telecom Access Point"
          skipLinks={[
            <a key="main" href="#main-content">
              Skip to main content
            </a>,
          ]}
          logoLinkElement={<Link href="/" title="Government of British Columbia" prefetch={false} />}
        >
          <div className="dashboard-header__user">
            <UserCircle2 size={20} aria-hidden="true" />
            <span>{displayName}</span>
            <button
              onClick={() => {
                window.location.href = "/auth/logout";
              }}
              className="dashboard-header__logout"
            >
              Logout
            </button>
          </div>
        </Header>

        <div className="dashboard-content">
          <main id="main-content" className="dashboard-main">
            <div className="dashboard-main__header">
              <div>
                <Heading level={1}>Telecom Spend Dashboard</Heading>
                <p className="dashboard-main__intro">
                  You are signed in as {displayName}. Spend is shown in millions of dollars and
                  sorted by highest total service category spend.
                </p>
              </div>
            </div>

            <section className="dashboard-controls" aria-label="Spend chart filters">
              <label className="dashboard-control">
                <span>Year type</span>
                <select
                  value={yearType}
                  onChange={(event) => {
                    const nextYearType = event.target.value as YearType;
                    const nextYears = buildYearOptions(nextYearType);
                    setYearType(nextYearType);
                    setYear((currentYear) =>
                      nextYears.includes(currentYear) ? currentYear : nextYears[nextYears.length - 1]
                    );
                    setQuarter("all");
                  }}
                >
                  <option value="fiscal">Fiscal</option>
                  <option value="calendar">Calendar</option>
                </select>
              </label>

              <label className="dashboard-control">
                <span>{yearLabel}</span>
                <select value={year} onChange={(event) => setYear(Number(event.target.value))}>
                  {yearOptions.map((option) => (
                    <option key={option} value={option}>
                      {yearType === "fiscal" ? `FY ${option}` : option}
                    </option>
                  ))}
                </select>
              </label>

              <label className="dashboard-control">
                <span>Quarter</span>
                <select value={quarter} onChange={(event) => setQuarter(event.target.value)}>
                  <option value="all">All quarters</option>
                  <option value="1">Q1</option>
                  <option value="2">Q2</option>
                  <option value="3">Q3</option>
                  <option value="4">Q4</option>
                </select>
              </label>
            </section>

            {chartQuery.isError ? (
              <div className="dashboard-alert" role="alert">
                Unable to load service category spend data.
              </div>
            ) : null}

            <section className="dashboard-chart-grid" aria-live="polite">
              <article className="dashboard-card">
                <div className="dashboard-card__header">
                  <h2>Plotly.js stacked bar</h2>
                  <p>Total spend by service category and vendor.</p>
                </div>
                <div className="dashboard-card__chart">
                  {chartQuery.isLoading ? (
                    <p className="dashboard-card__empty">Loading Plotly chart...</p>
                  ) : chartQuery.data?.plotly ? (
                    <Plot
                      data={chartQuery.data.plotly.data}
                      layout={{
                        ...chartQuery.data.plotly.layout,
                        autosize: true,
                        paper_bgcolor: "rgba(0,0,0,0)",
                        plot_bgcolor: "rgba(0,0,0,0)",
                      }}
                      config={{ displayModeBar: false, responsive: true }}
                      style={{ width: "100%", height: "420px" }}
                      useResizeHandler
                    />
                  ) : (
                    <p className="dashboard-card__empty">No Plotly data for this period.</p>
                  )}
                </div>
              </article>

              <article className="dashboard-card">
                <div className="dashboard-card__header">
                  <h2>Recharts stacked bar</h2>
                  <p>The same dataset, shaped for Recharts.</p>
                </div>
                <div className="dashboard-card__chart">
                  {chartQuery.isLoading ? (
                    <p className="dashboard-card__empty">Loading Recharts chart...</p>
                  ) : chartQuery.data?.recharts ? (
                    <ResponsiveContainer width="100%" height={420}>
                      <BarChart
                        data={chartQuery.data.recharts.data}
                        margin={{ top: 24, right: 24, bottom: 88, left: 48 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey={chartQuery.data.recharts.xAxisKey}
                          angle={-28}
                          textAnchor="end"
                          interval={0}
                          height={88}
                        />
                        <YAxis
                          label={{
                            value: chartQuery.data.recharts.yAxisLabel,
                            angle: -90,
                            position: "insideLeft",
                          }}
                        />
                        <Tooltip formatter={(value) => [`$${Number(value).toFixed(2)}M`, "Spend"]} />
                        <Legend />
                        {chartQuery.data.recharts.bars.map((bar) => (
                          <Bar
                            key={bar.dataKey}
                            dataKey={bar.dataKey}
                            stackId={bar.stackId}
                            fill={bar.fill}
                            name={bar.name}
                          />
                        ))}
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="dashboard-card__empty">No Recharts data for this period.</p>
                  )}
                </div>
              </article>
            </section>
          </main>
          <MinimalFooter />
        </div>
      </div>
    </div>
  );
}
