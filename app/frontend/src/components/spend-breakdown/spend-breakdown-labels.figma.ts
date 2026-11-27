// url=https://www.figma.com/design/ZQyCDzYcn4kl2d8c1dMzM6/TAP-design-file?node-id=39-69
// source=src/components/spend-breakdown/index.tsx
// component=SpendBreakdownLabels
/// <reference types="@figma/code-connect/figma-types-no-require" />
import figma from "figma";

// The labels are built from data, so the snippet passes the items list rather
// than the sample TELUS/Rogers text in the design.
export default {
  id: "SpendBreakdownLabels",
  imports: ['import { SpendBreakdownLabels } from "@/components/spend-breakdown";'],
  example: figma.code`<SpendBreakdownLabels items={providerSpend} />`,
  metadata: {
    nestable: true,
  },
};
