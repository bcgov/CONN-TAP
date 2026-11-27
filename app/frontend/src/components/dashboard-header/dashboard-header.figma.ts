// url=https://www.figma.com/design/ZQyCDzYcn4kl2d8c1dMzM6/TAP-design-file?node-id=14-924
// source=src/components/dashboard-header/index.tsx
// component=DashboardHeader
/// <reference types="@figma/code-connect/figma-types-no-require" />
import figma from "figma";

export default {
  id: "DashboardHeader",
  imports: ['import { DashboardHeader } from "@/components/dashboard-header";'],
  example: figma.code`<DashboardHeader displayName={displayName} orgName={orgName} />`,
  metadata: {
    nestable: true,
  },
};
