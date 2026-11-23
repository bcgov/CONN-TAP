export type DatasetEnvelope = {
  metadata: {
    chart?: unknown;
    table?: unknown;
  };
};

/** Load one dataset from the backend, optionally for the given months (`YYYY-MM`). */
export const fetchDataset = async (
  datasetId: string,
  filters: { period?: string[] } = {},
): Promise<DatasetEnvelope> => {
  const params = new URLSearchParams();
  for (const period of filters.period ?? []) params.append("period", period);

  const response = await fetch(
    `/api/v1/datasets/${datasetId}/data?${params.toString()}`,
    { cache: "no-store" },
  );

  if (!response.ok) {
    throw new Error(`Dataset request failed with status ${response.status}`);
  }

  return (await response.json()) as DatasetEnvelope;
};
