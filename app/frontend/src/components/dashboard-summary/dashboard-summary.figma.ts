// url=https://www.figma.com/design/ZQyCDzYcn4kl2d8c1dMzM6/TAP-design-file?node-id=14-807
// source=src/components/dashboard-summary/index.tsx
// component=DashboardSummary
/// <reference types="@figma/code-connect/figma-types-no-require" />
import figma from "figma";

export default {
  id: "DashboardSummary",
  imports: [
    'import { DashboardSummary } from "@/components/dashboard-summary";',
    'import { SpendBreakdown } from "@/components/spend-breakdown";',
    'import { SummaryStat } from "@/components/summary-stat";',
    'import { ReportingStatus } from "@/components/reporting-status";',
  ],
  example: figma.code`<DashboardSummary>
  <SpendBreakdown totalMillions={totalMillions} items={providerSpend} />
  <SummaryStat label={label} value={value} detail={detail} />
  <ReportingStatus receivedCount={receivedCount} expectedCount={expectedCount} />
</DashboardSummary>`,
  metadata: {
    nestable: false,
  },
};
