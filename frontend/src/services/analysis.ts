import api from "@/lib/api";


export interface AnalysisData {
  id: number;
  dataset_id: number;

  summary: Record<string, any>;

  column_info: Record<string, any>;

  statistics: Record<string, any>;

  missing_values: Record<string, any>;

  duplicates: Record<string, any>;

  correlations?: Record<string, any>;

  outliers?: Record<string, any>;

  summary_text: string;

  quality_score: number;

  created_at: string;
}


export async function getAnalysis(
  datasetId: number
) {
  const response = await api.get<AnalysisData>(
    `/analysis/${datasetId}`
  );

  return response.data;
}