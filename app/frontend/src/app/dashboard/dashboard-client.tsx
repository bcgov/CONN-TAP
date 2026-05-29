"use client";

import { Header, Heading } from "@bcgov/design-system-react-components";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import dynamic from "next/dynamic";
import { UserCircle2 } from "lucide-react";
import { DashboardSidebar } from "@/components/dashboard-sidebar";
import { MinimalFooter } from "@/components/minimal-footer";
import { MultiSelectDropdown } from "@/components/multi-select-dropdown";
import { ProviderLegend, type ProviderItem } from "@/components/provider-legend";
import {
  applyOutsideLabels,
  isPlotlyChart,
  isRechartsChart,
  type RechartsChart,
} from "@/lib/chart-utils";
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
import { fetchDataset } from "@/lib/dataset-api";
import { buildYearOptions, currentFiscalYear, type YearType } from "@/lib/date-utils";
import { useProviderToggle } from "@/lib/use-provider-toggle";
import { useEffect, useMemo, useRef, useState } from "react";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export function DashboardClient({ displayName }: { displayName: string }) {
  const [yearType, setYearType] = useState<YearType>("fiscal");
  const [years, setYears] = useState<string[]>([String(currentFiscalYear())]);
  const [quarters, setQuarters] = useState<string[]>([]);
  const PROVIDERS: ProviderItem[] = [
    { label: "Telus", traceName: "TELUS", color: "#b6f396" },
    { label: "Rogers", traceName: "Rogers", color: "#e02b24" },
  ];
  const { activeProviders, toggleProvider } = useProviderToggle(PROVIDERS.map((p) => p.traceName));

  const yearOptions = useMemo(() => buildYearOptions(yearType), [yearType]);
  const chartQuery = useQuery({
    queryKey: ["service-category-spend", yearType, years, quarters],
    queryFn: async () => {
      const [plotly, recharts] = await Promise.all([
        fetchDataset("service-category-spend-plotly", yearType, years, quarters),
        fetchDataset("service-category-spend-recharts", yearType, years, quarters),
      ]);
      return {
        plotly: isPlotlyChart(plotly.metadata.chart) ? plotly.metadata.chart : null,
        recharts: isRechartsChart(recharts.metadata.chart) ? recharts.metadata.chart : null,
      };
    },
  });

  const yearLabel = yearType === "fiscal" ? "Fiscal year" : "Calendar year";

  const chartContainerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = chartContainerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => window.dispatchEvent(new Event("resize")));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

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
                    const nextYearOptions = buildYearOptions(nextYearType);
                    setYearType(nextYearType);
                    setYears((prev) => {
                      const valid = prev.filter((y) => nextYearOptions.includes(Number(y)));
                      return valid.length > 0 ? valid : [String(nextYearOptions[nextYearOptions.length - 1])];
                    });
                    setQuarters([]);
                  }}
                >
                  <option value="fiscal">Fiscal</option>
                  <option value="calendar">Calendar</option>
                </select>
              </label>

              <div className="dashboard-control">
                <span>{yearLabel}</span>
                <MultiSelectDropdown
                  options={yearOptions.map((y) => ({
                    label: yearType === "fiscal" ? `FY ${y}` : String(y),
                    value: String(y),
                  }))}
                  selected={years}
                  onChange={setYears}
                  placeholder="All years"
                />
              </div>

              <div className="dashboard-control">
                <span>Quarter</span>
                <MultiSelectDropdown
                  options={[
                    { label: "Q1", value: "1" },
                    { label: "Q2", value: "2" },
                    { label: "Q3", value: "3" },
                    { label: "Q4", value: "4" },
                  ]}
                  selected={quarters}
                  onChange={setQuarters}
                  allLabel="All quarters"
                  placeholder="All quarters"
                />
              </div>
            </section>

            {chartQuery.isError ? (
              <div className="dashboard-alert" role="alert">
                Unable to load service category spend data.
              </div>
            ) : null}

            <section className="dashboard-chart-grid" aria-live="polite">
              <article className="dashboard-card" ref={chartContainerRef}>
                <div className="dashboard-card__header">
                  <h2>Spend by service category</h2>
                  <p>
                    The chart shows the breakdown of Telecom spend by service category and
                    highlighting how much is spent with each provider.
                  </p>
                  <ProviderLegend providers={PROVIDERS} activeProviders={activeProviders} onToggle={toggleProvider} />
                </div>
                <div className="dashboard-card__chart">
                  {chartQuery.isLoading ? (
                    <p className="dashboard-card__empty">Loading Plotly chart...</p>
                  ) : chartQuery.data?.plotly ? (
                    <Plot
                      data={applyOutsideLabels(chartQuery.data.plotly.data, activeProviders)}
                      layout={{
                        ...chartQuery.data.plotly.layout,
                        autosize: true,
                        showlegend: false,
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
                  <h2>Spend by service category</h2>
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
