// url=https://www.figma.com/design/ZQyCDzYcn4kl2d8c1dMzM6/TAP-design-file?node-id=39-71
// source=src/components/spend-breakdown/index.tsx
// component=SpendTotal
/// <reference types="@figma/code-connect/figma-types-no-require" />
import figma from "figma";

export default {
  id: "SpendTotal",
  imports: ['import { SpendTotal } from "@/components/spend-breakdown";'],
  example: figma.code`<SpendTotal totalMillions={totalMillions} />`,
  metadata: {
    nestable: true,
  },
};
