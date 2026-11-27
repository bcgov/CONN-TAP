// url=https://www.figma.com/design/ZQyCDzYcn4kl2d8c1dMzM6/TAP-design-file?node-id=39-78
// source=src/components/summary-stat/index.tsx
// component=SummaryStat
/// <reference types="@figma/code-connect/figma-types-no-require" />
import figma from "figma";

export default {
  id: "SummaryStat",
  imports: ['import { SummaryStat } from "@/components/summary-stat";'],
  example: figma.code`<SummaryStat label={label} value={value} detail={detail} />`,
  metadata: {
    nestable: true,
  },
};
