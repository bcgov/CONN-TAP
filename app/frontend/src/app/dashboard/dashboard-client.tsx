"use client";

import { Header, Heading } from "@bcgov/design-system-react-components";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { UserCircle2 } from "lucide-react";
import { ConfidentialityBanner } from "@/components/confidentiality-banner";
import { DashboardSidebar } from "@/components/dashboard-sidebar";
import { MinimalFooter } from "@/components/minimal-footer";
import { SpendIndicatorCards } from "@/components/spend-indicator-cards";
import { SpendTimelineBrush } from "@/components/spend-timeline-brush";
import { SpendByCategory } from "@/components/spend-by-category";
import { SpendBySector } from "@/components/spend-by-sector";
import { SpendByBge } from "@/components/spend-by-bge";
import { SpendSummaryTable } from "@/components/spend-summary-table";
import {
  isBgeChart,
  isIndicatorChart,
  isPlotlyChart,
  isSectorChart,
  isSummaryTable,
  isTimelineChart,
} from "@/lib/chart-utils";
import {
  buildPeriodRangeLabel,
  type YearType,
} from "@/lib/date-utils";
import { useEffect, useRef, useState } from "react";

type DatasetEnvelope = {
  metadata: {
    chart?: unknown;
    table?: unknown;
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

export function DashboardClient({
  displayName,
  visibleDatasetIds,
}: {
  displayName: string;
  visibleDatasetIds: string[];
}) {
  const [yearType, setYearType] = useState<YearType>("fiscal");
  const [period, setPeriods] = useState<string[]>([]);
  const canAccessBgeData = visibleDatasetIds.includes("spend-by-bge");
  const canAccessSummary = visibleDatasetIds.includes("spend-summary");

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

  const bgeQuery = useQuery({
    queryKey: ["spend-by-bge", yearType, period],
    queryFn: async () => {
      const result = await fetchDataset("spend-by-bge", { yearType, period });
      return isBgeChart(result.metadata.chart) ? result.metadata.chart : null;
    },
    enabled: canAccessBgeData && period.length > 0,
  });

  const summaryQuery = useQuery({
    queryKey: ["spend-summary", yearType, period],
    queryFn: async () => {
      const result = await fetchDataset("spend-summary", {
        yearType,
        period,
      });
      return isSummaryTable(result.metadata.table)
        ? result.metadata.table
        : null;
    },
    enabled: canAccessSummary && period.length > 0,
  });

  const dateRangeLabel = buildPeriodRangeLabel(period, yearType);

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
    <div className="dashboard-page">
      <ConfidentialityBanner />
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
                    Consolidated view of telecom spend across Buyers Group Entities
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
                dateRangeLabel={dateRangeLabel}
                isLoading={indicatorQuery.isLoading}
              />

              <section className="dashboard-chart-grid" aria-live="polite">
                <SpendByCategory
                  chart={chartQuery.data?.plotly}
                  dateRangeLabel={dateRangeLabel}
                  isLoading={chartQuery.isLoading}
                  isError={chartQuery.isError}
                />

                <SpendBySector
                  chart={sectorQuery.data}
                  dateRangeLabel={dateRangeLabel}
                  isLoading={sectorQuery.isLoading}
                  isError={sectorQuery.isError}
                />
              </section>

              {canAccessBgeData && (
                <section
                  className="dashboard-chart-grid dashboard-chart-grid--full"
                  aria-live="polite"
                >
                  <SpendByBge
                    chart={bgeQuery.data}
                    dateRangeLabel={dateRangeLabel}
                    isLoading={bgeQuery.isLoading}
                    isError={bgeQuery.isError}
                  />
                </section>
              )}

              {canAccessSummary && (
                <section
                  className="dashboard-chart-grid dashboard-chart-grid--full"
                  aria-live="polite"
                >
                  <SpendSummaryTable
                    table={summaryQuery.data}
                    dateRangeLabel={dateRangeLabel}
                    isLoading={summaryQuery.isLoading}
                    isError={summaryQuery.isError}
                  />
                </section>
              )}
            </main>
            <MinimalFooter />
          </div>
        </div>
      </div>
    </div>
  );
}
