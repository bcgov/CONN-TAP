"use client";

import { useQuery } from "@tanstack/react-query";
import { DashboardSummary } from "@/components/dashboard-summary";
import { FilterPanel } from "@/components/filter-panel";
import { PendingReportsTable } from "@/components/pending-reports-table";
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

type MissingReport = {
  report: string;
  provider: string;
  service_type: string;
  frequency: "monthly" | "quarterly";
  period: string;
};

type ReportingStatusData = {
  expected_count: number;
  received_count: number;
  missing: MissingReport[];
};

// How many vendor reports are expected for the months, and which ones haven't come in.
const fetchReportingStatus = async (periods: string[]): Promise<ReportingStatusData> => {
  const result = await fetchDataset("reporting-status", { period: periods });
  return result.metadata as ReportingStatusData;
};

// Monthly reports (TELUS and Rogers NGTA) share one table; each quarterly report
// (TSMA, TSMA Lite) gets its own.
const MONTHLY_REPORT_COLUMNS = [
  { key: "provider", label: "Provider" },
  { key: "service_type", label: "Service type" },
  { key: "period", label: "Reporting month" },
];
const QUARTERLY_REPORT_COLUMNS = [{ key: "period", label: "Reporting period" }];

export function BgeDashboardClient() {
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

  const reportingStatusQuery = useQuery({
    queryKey: ["reporting-status", periods],
    queryFn: () => fetchReportingStatus(periods),
    enabled: periods.length > 0,
  });
  const reportingStatus = reportingStatusQuery.data;
  const missingReports = reportingStatus?.missing ?? [];
  const missingMonthlyReports = missingReports.filter((missing) => missing.frequency === "monthly");
  const missingQuarterlyReports = missingReports.filter((missing) => missing.frequency === "quarterly");
  const quarterlyReportNames = [...new Set(missingQuarterlyReports.map((missing) => missing.report))];
  const reportingPeriod = formatPeriodRange(periods);

  return (
    <div className="bge-dashboard__body">
      <FilterPanel />

      <div className="dashboard-content">
        <main id="main-content" className="dashboard-main">
          <div className="bge-dashboard__heading">
            <h1 className="bge-dashboard__title">Telecom Spend Dashboard</h1>
            <p className="bge-dashboard__period">
              Reporting Period: {reportingPeriod || "–"}
            </p>
          </div>

          <DashboardSummary>
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
            <ReportingStatus
              receivedCount={reportingStatus?.received_count}
              expectedCount={reportingStatus?.expected_count}
            >
              {missingReports.length > 0 ? (
                <>
                  {missingMonthlyReports.length > 0 && (
                    <PendingReportsTable
                      title="Pending NGTA reports"
                      description={`Monthly reports not included in dashboard totals for ${reportingPeriod}`}
                      columns={MONTHLY_REPORT_COLUMNS}
                      rows={missingMonthlyReports}
                    />
                  )}
                  {quarterlyReportNames.map((reportName) => (
                    <PendingReportsTable
                      key={reportName}
                      title={`Pending ${reportName} reports`}
                      description={`Quarterly reports not included in dashboard totals for ${reportingPeriod}`}
                      columns={QUARTERLY_REPORT_COLUMNS}
                      rows={missingQuarterlyReports.filter((missing) => missing.report === reportName)}
                    />
                  ))}
                </>
              ) : undefined}
            </ReportingStatus>
          </DashboardSummary>
        </main>
      </div>
    </div>
  );
}
