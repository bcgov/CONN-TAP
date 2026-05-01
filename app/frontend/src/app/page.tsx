"use client";

import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { Button } from "@bcgov/design-system-react-components";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

type DatasetResponse = {
  columns: string[];
  rows: (string | number | null)[][];
  row_count: number;
  metadata: Record<string, unknown>;
};

async function fetchIspSpending(): Promise<DatasetResponse> {
  const res = await fetch("/api/v1/datasets/isp-spending/data");
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export default function HomePage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["isp-spending"],
    queryFn: fetchIspSpending,
  });

  const colIndex = (name: string) => data?.columns.indexOf(name) ?? -1;
  const regionIdx = colIndex("region");
  const totalIdx = colIndex("total_spend");

  const x =
    data && regionIdx >= 0 ? data.rows.map((r) => String(r[regionIdx] ?? "")) : [];
  const y =
    data && totalIdx >= 0 ? data.rows.map((r) => Number(r[totalIdx] ?? 0)) : [];

  return (
    <main>
      <h1>Data Management Platform</h1>
      <p>ISP spending rows: {isLoading ? "…" : data?.row_count ?? 0}</p>
      <Button onPress={() => refetch()}>Refresh</Button>

      {error && <p style={{ color: "red" }}>{(error as Error).message}</p>}

      {data && x.length > 0 && (
        <Plot
          data={[{ type: "bar", x, y }]}
          layout={{ title: "ISP spending by region/year", autosize: true }}
          style={{ width: "100%", height: 420 }}
          useResizeHandler
        />
      )}
    </main>
  );
}
