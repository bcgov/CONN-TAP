// url=https://www.figma.com/design/ZQyCDzYcn4kl2d8c1dMzM6/TAP-design-file?node-id=14-864
// source=src/components/confidentiality-banner/index.tsx
// component=ConfidentialityBanner
/// <reference types="@figma/code-connect/figma-types-no-require" />
import figma from "figma";

// The Figma "Banner" has no component properties; its title and message match
// the component's defaults, so the snippet needs no props.
export default {
  id: "ConfidentialityBanner",
  imports: [
    'import { ConfidentialityBanner } from "@/components/confidentiality-banner";',
  ],
  example: figma.code`<ConfidentialityBanner />`,
  metadata: {
    nestable: true,
  },
};
