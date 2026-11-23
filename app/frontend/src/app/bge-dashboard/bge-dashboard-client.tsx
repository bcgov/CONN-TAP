"use client";

import { useQuery } from "@tanstack/react-query";
import { ConfidentialityBanner } from "@/components/confidentiality-banner";
import { DashboardHeader } from "@/components/dashboard-header";
import { DashboardSidebar } from "@/components/dashboard-sidebar";
import { FilterPanel } from "@/components/filter-panel";
import { MinimalFooter } from "@/components/minimal-footer";
import { ReportingStatus } from "@/components/reporting-status";
import { SpendBreakdown } from "@/components/spend-breakdown";
import { SummaryStat } from "@/components/summary-stat";
import {
  isIndicatorChart,
  isTimelineChart,
  type TimelinePoint,
  VENDOR_COLOURS,
} from "@/lib/chart-utils";
import { formatPeriodRange } from "@/lib/date-utils";
import { fetchDataset } from "@/lib/fetch-dataset";
import { fmtMillions } from "@/lib/format-utils";

// Same default as the main dashboard: the latest 12 months that have data.
const DEFAULT_MONTHS = 12;

// Total spend per month, for every month that has data.
const fetchMonthlySpend = async (): Promise<TimelinePoint[]> => {
  const result = await fetchDataset("total-spend-over-time");
  const chart = result.metadata.chart;
  return isTimelineChart(chart) ? chart.data : [];
};

export function BgeDashboardClient({
  displayName,
  orgName,
  isAdmin = false,
}: {
  displayName: string;
  orgName?: string;
  isAdmin?: boolean;
}) {
  const monthlySpendQuery = useQuery({
    queryKey: ["monthly-spend"],
    queryFn: fetchMonthlySpend,
  });
  const months = (monthlySpendQuery.data ?? []).slice(-DEFAULT_MONTHS);
  const periods = months.map((month) => month.period);
  const peakMonth = months.length
    ? months.reduce((peak, month) => (month.value > peak.value ? month : peak))
    : undefined;

  const spendQuery = useQuery({
    queryKey: ["isp-spend-indicators", periods],
    queryFn: async () => {
      const result = await fetchDataset("isp-spend-indicators", { period: periods });
      // Same shape as the main dashboard's query, since both share this cache key.
      return isIndicatorChart(result.metadata.chart) ? result.metadata.chart : null;
    },
    enabled: periods.length > 0,
  });
  const indicators = spendQuery.data?.indicators ?? [];
  const totalMillions = indicators.find((indicator) => !indicator.provider)?.value_millions ?? 0;
  const providerSpend = indicators
    .filter((indicator) => indicator.provider)
    .map((indicator) => ({
      label: indicator.provider ?? "",
      valueMillions: indicator.value_millions,
      percentage: totalMillions ? (indicator.value_millions / totalMillions) * 100 : 0,
      colour: VENDOR_COLOURS[indicator.provider ?? ""],
    }));

  return (
    <div className="dashboard-page">
      <ConfidentialityBanner />
      <div className="dashboard-shell">
        <DashboardSidebar showAdmin={isAdmin} />

        <div className="dashboard-right">
          <DashboardHeader displayName={displayName} orgName={orgName} />

          <div className="bge-dashboard__body">
            <FilterPanel />

            <div className="dashboard-content">
              <main id="main-content" className="dashboard-main">
                <div className="bge-dashboard__heading">
                  <h1 className="bge-dashboard__title">Telecom Spend Dashboard</h1>
                  <p className="bge-dashboard__period">
                    Reporting Period: {formatPeriodRange(periods) || "–"}
                  </p>
                </div>

                <section className="bge-dashboard__summary" aria-label="Dashboard summary">
                  <SpendBreakdown
                    isLoading={!spendQuery.data}
                    totalMillions={totalMillions}
                    items={providerSpend}
                  />
                  <SummaryStat
                    label="Peak Month"
                    value={peakMonth?.label ?? "—"}
                    detail={peakMonth ? fmtMillions(peakMonth.value) : undefined}
                  />
                  <ReportingStatus />
                </section>
              </main>
              <MinimalFooter />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
