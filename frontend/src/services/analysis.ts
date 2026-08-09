import api from "@/lib/api";

// =========================
// Missing Value Information
// =========================

export interface MissingValueInfo {
  count: number;
  percent: number;
}

// =========================
// Duplicate Information
// =========================

export interface DuplicateInfo {
  count: number;
  percent?: number;
  [key: string]: any;
}

// =========================
// Analysis Data
// =========================

export interface AnalysisData {
  id: number;
  dataset_id: number;

  summary: {
    rows: number;
    columns: number;
    memory_usage?: number;
    [key: string]: any;
  };

  column_info: Record<string, any>;

  statistics: Record<string, any>;

  missing_values: Record<
    string,
    MissingValueInfo
  >;

  duplicates: DuplicateInfo;

  correlations?: Record<string, any>;

  outliers?: Record<string, any>;

  summary_text: string;

  quality_score: number;

  created_at: string;
}

// =========================
// Get Analysis
// =========================

export async function getAnalysis(
  datasetId: number
): Promise<AnalysisData> {
  const response = await api.get<AnalysisData>(
    `/analysis/${datasetId}`
  );

  return response.data;
}
