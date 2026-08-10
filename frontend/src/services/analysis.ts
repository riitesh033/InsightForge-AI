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
  has_duplicates?: boolean;
  percent?: number;
  [key: string]: any;
}

// =========================
// Column Information
// =========================

export interface ColumnInfo {
  name: string;
  dtype: string;
  unique: number;
  missing: number;
  missing_percent?: number;
  memory_usage?: number;

  // Numeric columns
  mean?: number | null;
  std?: number | null;
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
    missing_cells?: number;
    duplicate_rows?: number;
    [key: string]: any;
  };

  // Backend returns an array of column information
  column_info: ColumnInfo[];

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