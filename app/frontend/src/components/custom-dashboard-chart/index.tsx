"use client";

import { useRef } from "react";
import { ChartDownloadButton } from "@/components/chart-download-button";

type CustomDashboardChartProps = {
  title: string;
  label?: string;
  children: React.ReactNode;
};

export function CustomDashboardChart({ title, label, children }: CustomDashboardChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  return (
    <>
      <ChartDownloadButton targetRef={ref} title={title} label={label} />
      <div ref={ref}>{children}</div>
    </>
  );
}
