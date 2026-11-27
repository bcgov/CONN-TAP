// url=https://www.figma.com/design/ZQyCDzYcn4kl2d8c1dMzM6/TAP-design-file?node-id=43-247
// source=src/components/minimal-footer/index.tsx
// component=MinimalFooter
/// <reference types="@figma/code-connect/figma-types-no-require" />
import figma from "figma";

// The footer has no Figma properties; it shows the standard B.C. Government
// links by default, or pass `links` to use different ones.
export default {
  id: "MinimalFooter",
  imports: ['import { MinimalFooter } from "@/components/minimal-footer";'],
  example: figma.code`<MinimalFooter />`,
  metadata: {
    nestable: true,
  },
};
