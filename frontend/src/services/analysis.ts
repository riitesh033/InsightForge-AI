import api from "./api";

export interface Analysis {
  id: number;
  dataset_id: number;
  summary: any;
  summary_text: string;
  quality_score: number;
  column_info: any[];
  statistics: any;
  missing_values: any;
  duplicates: any;
  correlations: any;
  outliers: any;
}

export async function getAnalysis(datasetId: number) {
  try {
    console.log("Fetching analysis for:", datasetId);

    const response = await api.get(
      `/api/v1/analysis/${datasetId}`
    );

    console.log("Response:", response.data);

    return response.data as Analysis;
  } catch (error: any) {
    console.error("API Error:", error);

    if (error.response) {
      console.error("Status:", error.response.status);
      console.error("Data:", error.response.data);
    }

    throw error;
  }
}