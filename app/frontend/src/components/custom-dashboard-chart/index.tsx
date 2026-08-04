"use client";

import { useId, useRef, useState } from "react";
import { Tab, Tabs } from "@mui/material";
import { ChartDownloadButton } from "@/components/chart-download-button";
import styles from "./custom-dashboard-chart.module.css";

export type ChartState = {
  isLoading: boolean;
  isError?: boolean;
  isEmpty: boolean;
  loadingLabel: string;
  errorLabel?: string;
  emptyLabel: string;
};

// Loading / error / empty placeholder, or the view itself when there's data.
const stateView = (state: ChartState | undefined, view: React.ReactNode) => {
  if (!state) return view;
  if (state.isLoading)
    return <p className="dashboard-card__empty">{state.loadingLabel}</p>;
  if (state.isError && state.errorLabel)
    return <p className="dashboard-card__empty">{state.errorLabel}</p>;
  if (state.isEmpty)
    return <p className="dashboard-card__empty">{state.emptyLabel}</p>;
  return view;
};

type CustomDashboardChartProps = {
  title: string;
  label?: string;
  downloadable?: boolean;
  header?: React.ReactNode;
  table?: React.ReactNode;
  tabsLabel?: string;
  // Applied to whichever view is active, so a card declares its loading /
  // error / empty handling once instead of per tab.
  state?: ChartState;
  children: React.ReactNode;
};

export function CustomDashboardChart({
  title,
  label,
  downloadable = true,
  header,
  table,
  tabsLabel = "Chart view",
  state,
  children,
}: CustomDashboardChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [view, setView] = useState(0);
  // Unique per instance so tab/panel ids stay distinct across cards.
  const baseId = useId();

  // Temp disable download until we add functionality
  const showDownload = downloadable && (!table || view === 0);

  const downloadButton = showDownload && (
    <ChartDownloadButton
      targetRef={ref}
      title={title}
      label={label}
      floating={!table}
    />
  );

  if (!table) {
    return (
      <>
        {downloadButton}
        <div ref={ref}>
          {header}
          {stateView(state, children)}
        </div>
      </>
    );
  }

  return (
    <>
      <div className={styles.toolbar}>
        <Tabs
          value={view}
          onChange={(_event, next: number) => setView(next)}
          aria-label={tabsLabel}
        >
          {["Graph", "Table"].map((tabLabel, index) => (
            <Tab
              key={tabLabel}
              label={tabLabel}
              id={`${baseId}-tab-${index}`}
              aria-controls={`${baseId}-tabpanel-${index}`}
            />
          ))}
        </Tabs>
        {downloadButton}
      </div>

      <div ref={ref} className={styles.content}>
        {header}
        {[
          { key: "graph", content: children },
          { key: "table", content: table },
        ].map((panel, index) => (
          // Render both panels so every tab's aria-controls resolves; hide the
          // inactive one and only mount the active tab's content.
          <div
            key={panel.key}
            role="tabpanel"
            hidden={view !== index}
            id={`${baseId}-tabpanel-${index}`}
            aria-labelledby={`${baseId}-tab-${index}`}
          >
            {view === index && stateView(state, panel.content)}
          </div>
        ))}
      </div>
    </>
  );
}
