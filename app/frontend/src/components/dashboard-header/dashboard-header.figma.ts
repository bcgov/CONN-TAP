// url=https://www.figma.com/design/ZQyCDzYcn4kl2d8c1dMzM6/TAP-design-file?node-id=14-924
// source=src/components/dashboard-header/index.tsx
// component=DashboardHeader
/// <reference types="@figma/code-connect/figma-types-no-require" />
import figma from "figma";

const instance = figma.selectedInstance;

// The Figma "Header" has no component properties; the user's name and
// organization come from its text layers.
function getText(layerName: string) {
  const layer = instance.findText(layerName);
  return layer.type === "TEXT" ? layer.textContent : layerName;
}

const displayName = getText("IDIR User");
const orgName = getText("Buyers Group Entity");

export default {
  id: "DashboardHeader",
  imports: [
    'import { DashboardHeader } from "@/components/dashboard-header";',
  ],
  example: figma.code`<DashboardHeader displayName="${displayName}" orgName="${orgName}" />`,
  metadata: {
    nestable: true,
  },
};
