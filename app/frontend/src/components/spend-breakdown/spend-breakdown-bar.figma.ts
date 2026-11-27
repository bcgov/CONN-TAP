// url=https://www.figma.com/design/ZQyCDzYcn4kl2d8c1dMzM6/TAP-design-file?node-id=39-70
// source=src/components/spend-breakdown/index.tsx
// component=SpendBreakdownBar
/// <reference types="@figma/code-connect/figma-types-no-require" />
import figma from "figma";

// The segments are sized and coloured from data, so the snippet passes the
// items list rather than the sample 63% / 37% split in the design.
export default {
  id: "SpendBreakdownBar",
  imports: ['import { SpendBreakdownBar } from "@/components/spend-breakdown";'],
  example: figma.code`<SpendBreakdownBar items={providerSpend} />`,
  metadata: {
    nestable: true,
  },
};
