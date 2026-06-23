"use client";

import { Header, Heading } from "@bcgov/design-system-react-components";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import dynamic from "next/dynamic";
import { UserCircle2 } from "lucide-react";
import { CustomDashboardChart } from "@/components/custom-dashboard-chart";
import { DashboardSidebar } from "@/components/dashboard-sidebar";
import { MinimalFooter } from "@/components/minimal-footer";
import { SpendIndicatorCards } from "@/components/spend-indicator-cards";
import { SpendTimelineBrush } from "@/components/spend-timeline-brush";
import { SpendBySectorChart } from "@/components/spend-by-sector-chart";
import { SpendByBgeChart } from "@/components/spend-by-bge-chart";
import {
  applyOutsideLabels,
  isBgeChart,
  isIndicatorChart,
  isPlotlyChart,
  isSectorChart,
  isTimelineChart,
} from "@/lib/chart-utils";
import {
  buildPeriodRangeLabel,
  periodsToYearsQuarters,
  type YearType,
} from "@/lib/date-utils";
import { useEffect, useRef, useState } from "react";

type DatasetEnvelope = {
  metadata: {
    chart?: unknown;
  };
};

async function fetchDataset(
  datasetId: string,
  filters: { yearType: YearType; period?: string[] },
) {
  const params = new URLSearchParams({ year_type: filters.yearType });
  for (const p of filters.period ?? []) params.append("period", p);

  const response = await fetch(
    `/api/v1/datasets/${datasetId}/data?${params.toString()}`,
    { cache: "no-store" },
  );

  if (!response.ok) {
    throw new Error(`Dataset request failed with status ${response.status}`);
  }

  return (await response.json()) as DatasetEnvelope;
}

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export function DashboardClient({ displayName }: { displayName: string }) {
  const [yearType, setYearType] = useState<YearType>("fiscal");
  const [period, setPeriods] = useState<string[]>([]);

  const chartQuery = useQuery({
    queryKey: ["service-category-spend", yearType, period],
    queryFn: async () => {
      const plotly = await fetchDataset("service-category-spend-plotly", {
        yearType,
        period,
      });
      return {
        plotly: isPlotlyChart(plotly.metadata.chart)
          ? plotly.metadata.chart
          : null,
      };
    },
    enabled: period.length > 0,
  });
  const indicatorQuery = useQuery({
    queryKey: ["isp-spend-indicators", yearType, period],
    queryFn: async () => {
      const result = await fetchDataset("isp-spend-indicators", {
        yearType,
        period,
      });
      return isIndicatorChart(result.metadata.chart)
        ? result.metadata.chart
        : null;
    },
  });

  const timelineQuery = useQuery({
    queryKey: ["total-spend-over-time", yearType],
    queryFn: async () => {
      const result = await fetchDataset("total-spend-over-time", { yearType });
      if (!isTimelineChart(result.metadata.chart)) return null;
      const chart = result.metadata.chart;
      return {
        ...chart,
        data: chart.data.filter(
          (p) => parseInt(p.period.split("_")[0]) >= 2024,
        ),
      };
    },
  });

  const sectorQuery = useQuery({
    queryKey: ["spend-by-sector", yearType, period],
    queryFn: async () => {
      const result = await fetchDataset("spend-by-sector", {
        yearType,
        period,
      });
      return isSectorChart(result.metadata.chart)
        ? result.metadata.chart
        : null;
    },
    enabled: period.length > 0,
  });
  const sectorTotalLabel = sectorQuery.data?.total_millions?.toFixed(1) ?? "—";

  const bgeQuery = useQuery({
    queryKey: ["spend-by-bge", yearType, period],
    queryFn: async () => {
      const result = await fetchDataset("spend-by-bge", { yearType, period });
      return isBgeChart(result.metadata.chart) ? result.metadata.chart : null;
    },
    enabled: period.length > 0,
  });

  const chartContainerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = chartContainerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() =>
      window.dispatchEvent(new Event("resize")),
    );
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
          logoLinkElement={
            <Link
              href="/"
              title="Government of British Columbia"
              prefetch={false}
            />
          }
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
                <Heading level={5}>TSMA & NGTA</Heading>
                <p className="dashboard-main__intro">
                  Consolidated view of telecom spend across BC government
                  entities
                </p>
              </div>
            </div>
            <hr className="dashboard-main__divider" />

            <section
              className="dashboard-controls"
              aria-label="Spend chart filters"
            >
              <label className="dashboard-control">
                <span>Year type</span>
                <select
                  value={yearType}
                  onChange={(e) => {
                    setYearType(e.target.value as YearType);
                    setPeriods([]);
                  }}
                >
                  <option value="fiscal">Fiscal</option>
                  <option value="calendar">Calendar</option>
                </select>
              </label>
            </section>

            <SpendTimelineBrush
              key={yearType}
              chart={timelineQuery.data ?? null}
              isLoading={timelineQuery.isLoading}
              onPeriodsChange={setPeriods}
              yAxisFormatter={(v) => `$${Number(v).toFixed(0)}M`}
              tooltipFormatter={(v) => `$${Number(v).toFixed(1)}M`}
            />

            <SpendIndicatorCards
              indicators={indicatorQuery.data?.indicators ?? []}
              dateRangeLabel={buildPeriodRangeLabel(period, yearType)}
              isLoading={indicatorQuery.isLoading}
            />

            {chartQuery.isError ? (
              <div className="dashboard-alert" role="alert">
                Unable to load service category spend data.
              </div>
            ) : null}

            <section className="dashboard-chart-grid" aria-live="polite">
              <article className="dashboard-card">
                <CustomDashboardChart
                  title="Spend by Service Category"
                  label="Download spend by service category chart as image"
                >
                  <div className="dashboard-card__header">
                    <h2>Spend by service category</h2>
                    {buildPeriodRangeLabel(period, yearType) && (
                      <p className="dashboard-card__date-range">
                        {buildPeriodRangeLabel(period, yearType)}
                      </p>
                    )}
                    <p>
                      The chart shows the breakdown of Telecom spend by service
                      category and highlighting how much is spent with each
                      provider.
                    </p>
                  </div>
                  <div className="dashboard-card__chart">
                    {chartQuery.isLoading ? (
                      <p className="dashboard-card__empty">
                        Loading Plotly chart...
                      </p>
                    ) : chartQuery.data?.plotly ? (
                      <Plot
                        data={applyOutsideLabels(
                          chartQuery.data.plotly.data,
                          new Set(
                            chartQuery.data.plotly.data.map(
                              (t) => (t as { name?: string }).name ?? "",
                            ),
                          ),
                        )}
                        layout={{
                          ...chartQuery.data.plotly.layout,
                          autosize: true,
                          showlegend: true,
                          legend: {
                            ...chartQuery.data.plotly.layout.legend,
                            itemclick: false,
                            itemdoubleclick: false,
                          },
                          paper_bgcolor: "rgba(0,0,0,0)",
                          plot_bgcolor: "rgba(0,0,0,0)",
                        }}
                        config={{ displayModeBar: false, responsive: true }}
                        style={{ width: "100%", height: "420px" }}
                        useResizeHandler
                      />
                    ) : (
                      <p className="dashboard-card__empty">
                        No Plotly data for this period.
                      </p>
                    )}
                  </div>
                </CustomDashboardChart>
              </article>

              <article className="dashboard-card">
                <CustomDashboardChart
                  title="Telecom Spend Share by Sector"
                  label="Download spend by sector chart as image"
                >
                  <div className="dashboard-card__header">
                    <h2>Telecom Spend share by Sector (${sectorTotalLabel}M)</h2>
                  </div>
                  <div className="dashboard-card__chart">
                    {sectorQuery.isLoading ? (
                      <p className="dashboard-card__empty">
                        Loading sector chart…
                      </p>
                    ) : sectorQuery.isError ? (
                      <p className="dashboard-card__empty">
                        Unable to load sector data.
                      </p>
                    ) : sectorQuery.data ? (
                      <SpendBySectorChart
                        chart={sectorQuery.data}
                        dateRangeLabel={buildPeriodRangeLabel(period, yearType)}
                      />
                    ) : (
                      <p className="dashboard-card__empty">
                        No data for this period.
                      </p>
                    )}
                  </div>
                </CustomDashboardChart>
              </article>
            </section>

            <section className="dashboard-chart-grid dashboard-chart-grid--full" aria-live="polite">
              <article className="dashboard-card">
                <CustomDashboardChart
                  title="Spend by BGE"
                  label="Download spend by BGE chart as image"
                >
                  <div className="dashboard-card__header">
                    <h2>Spend by BGE</h2>
                  </div>
                  <div className="dashboard-card__chart">
                    {bgeQuery.isLoading ? (
                      <p className="dashboard-card__empty">Loading BGE chart…</p>
                    ) : bgeQuery.isError ? (
                      <p className="dashboard-card__empty">
                        Unable to load BGE data.
                      </p>
                    ) : bgeQuery.data ? (
                      <SpendByBgeChart
                        chart={bgeQuery.data}
                        dateRangeLabel={buildPeriodRangeLabel(period, yearType)}
                      />
                    ) : (
                      <p className="dashboard-card__empty">
                        No data for this period.
                      </p>
                    )}
                  </div>
                </CustomDashboardChart>
              </article>
            </section>
          </main>
          <MinimalFooter />
        </div>
      </div>
    </div>
  );
}
