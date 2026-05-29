import type { YearType } from "./date-utils";

export type DatasetEnvelope = {
  metadata: {
    chart?: unknown;
  };
};

export async function fetchDataset(
  datasetId: string,
  yearType: YearType,
  years: string[],
  quarters: string[]
): Promise<DatasetEnvelope> {
  const params = new URLSearchParams({ year_type: yearType });

  for (const y of years) {
    params.append("years", y);
  }
  for (const q of quarters) {
    params.append("quarters", q);
  }

  const response = await fetch(`/api/v1/datasets/${datasetId}/data?${params.toString()}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Dataset request failed with status ${response.status}`);
  }

  return (await response.json()) as DatasetEnvelope;
}
