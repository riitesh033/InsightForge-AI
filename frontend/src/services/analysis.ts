import api from "./api";

export interface Analysis {
  id: number;
  dataset_id: number;
  summary: Record<string, any>;
  summary_text: string;
  column_info: any[];
  statistics: Record<string, any>;
  missing_values: Record<string, any>;
  duplicates: Record<string, any>;
  correlations: Record<string, any>;
  outliers: Record<string, any>;
}

export async function getAnalysis(
  datasetId: number
): Promise<Analysis> {
  const response = await api.get(
    `/api/v1/analysis/${datasetId}`
  );

  return response.data;
}