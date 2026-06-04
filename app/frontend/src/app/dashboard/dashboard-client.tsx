"use client";

import { Header, Heading } from "@bcgov/design-system-react-components";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import dynamic from "next/dynamic";
import { UserCircle2 } from "lucide-react";
import { DashboardSidebar } from "@/components/dashboard-sidebar";
import { MinimalFooter } from "@/components/minimal-footer";
import { MultiSelectDropdown } from "@/components/multi-select-dropdown";
import {
  applyOutsideLabels,
  isPlotlyChart,
} from "@/lib/chart-utils";
import { fetchDataset } from "@/lib/dataset-api";
import { buildYearOptions, currentFiscalYear, type YearType } from "@/lib/date-utils";

import { useEffect, useMemo, useRef, useState } from "react";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export function DashboardClient({ displayName }: { displayName: string }) {
  const [yearType, setYearType] = useState<YearType>("fiscal");
  const [years, setYears] = useState<string[]>([String(currentFiscalYear())]);
  const [quarters, setQuarters] = useState<string[]>([]);
const yearOptions = useMemo(() => buildYearOptions(yearType), [yearType]);
  const chartQuery = useQuery({
    queryKey: ["service-category-spend", yearType, years, quarters],
    queryFn: async () => {
      const plotly = await fetchDataset("service-category-spend-plotly", yearType, years, quarters);
      return {
        plotly: isPlotlyChart(plotly.metadata.chart) ? plotly.metadata.chart : null,
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
                    label: yearType === "fiscal" ? `FY ${y - 1}-${y}` : String(y),
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
                </div>
                <div className="dashboard-card__chart">
                  {chartQuery.isLoading ? (
                    <p className="dashboard-card__empty">Loading Plotly chart...</p>
                  ) : chartQuery.data?.plotly ? (
                    <Plot
                      data={applyOutsideLabels(
                        chartQuery.data.plotly.data,
                        new Set(chartQuery.data.plotly.data.map((t) => (t as { name?: string }).name ?? ""))
                      )}
                      layout={{
                        ...chartQuery.data.plotly.layout,
                        autosize: true,
                        showlegend: true,
                        legend: { ...chartQuery.data.plotly.layout.legend, itemclick: false, itemdoubleclick: false },
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

            </section>
          </main>
          <MinimalFooter />
        </div>
      </div>
    </div>
  );
}
