// url=https://www.figma.com/design/ZQyCDzYcn4kl2d8c1dMzM6/TAP-design-file?node-id=14-719
// source=src/components/reporting-status/index.tsx
// component=ReportingStatus
/// <reference types="@figma/code-connect/figma-types-no-require" />
import figma from "figma";

// Connected to the inner "Component 5", which is used both on its own (node
// 39:101) and inside "Section - Dashboard summary" (node 14:807).
export default {
  id: "ReportingStatus",
  imports: ['import { ReportingStatus } from "@/components/reporting-status";'],
  example: figma.code`<ReportingStatus receivedCount={receivedCount} expectedCount={expectedCount} />`,
  metadata: {
    nestable: true,
  },
};
