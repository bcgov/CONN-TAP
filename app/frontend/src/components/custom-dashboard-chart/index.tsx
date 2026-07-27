"use client";

import { useRef } from "react";
import { ChartDownloadButton } from "@/components/chart-download-button";

type CustomDashboardChartProps = {
  title: string;
  label?: string;
  // Set false to hide the image-download button (e.g. the summary table).
  downloadable?: boolean;
  children: React.ReactNode;
};

export function CustomDashboardChart({
  title,
  label,
  downloadable = true,
  children,
}: CustomDashboardChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  return (
    <>
      {downloadable && <ChartDownloadButton targetRef={ref} title={title} label={label} />}
      <div ref={ref}>{children}</div>
    </>
  );
}
