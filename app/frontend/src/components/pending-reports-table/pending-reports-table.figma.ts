// url=https://www.figma.com/design/ZQyCDzYcn4kl2d8c1dMzM6/TAP-design-file?node-id=42-199
// source=src/components/pending-reports-table/index.tsx
// component=PendingReportsTable
/// <reference types="@figma/code-connect/figma-types-no-require" />
import figma from "figma";

// The expanded view of Reporting Status: one PendingReportsTable per group of
// pending reports, passed to ReportingStatus as children.
export default {
  id: "ReportingStatusDetails",
  imports: [
    'import { ReportingStatus } from "@/components/reporting-status";',
    'import { PendingReportsTable } from "@/components/pending-reports-table";',
  ],
  example: figma.code`<ReportingStatus receivedCount={receivedCount} expectedCount={expectedCount}>
  {pendingReportGroups.map((group) => (
    <PendingReportsTable
      key={group.title}
      title={group.title}
      description={group.description}
      columns={group.columns}
      rows={group.rows}
    />
  ))}
</ReportingStatus>`,
  metadata: {
    nestable: false,
  },
};
