import api from "@/lib/api";


// ============================================================
// Dataset
// ============================================================

export interface DatasetReportInfo {
  dataset_id: number | null;
  filename: string | null;
  file_type: string | null;
  rows: number;
  columns: number;
}


// ============================================================
// Data Quality
// ============================================================

export interface MissingValueReport {
  column: string;
  count: number;
  percentage?: number | null;
}


export interface DuplicateReport {
  count: number;
  percentage?: number | null;
}


export interface DataQualityReport {
  quality_score?: number | null;

  missing_values: MissingValueReport[];

  duplicates?: DuplicateReport | null;

  invalid_values: Record<string, any>[];

  datatype_issues: Record<string, any>[];

  inconsistent_values: Record<string, any>[];
}


// ============================================================
// Statistics
// ============================================================

export interface DescriptiveStatistics {
  column: string;

  count?: number | null;

  mean?: number | null;

  median?: number | null;

  mode?: number | string | null;

  minimum?: number | null;

  maximum?: number | null;

  range?: number | null;

  standard_deviation?: number | null;

  variance?: number | null;

  q1?: number | null;

  q3?: number | null;

  iqr?: number | null;

  skewness?: number | null;

  kurtosis?: number | null;

  percentile_5?: number | null;

  percentile_95?: number | null;

  coefficient_of_variation?: number | null;
}


// ============================================================
// Correlations
// ============================================================

export interface CorrelationFinding {
  variable_a: string;

  variable_b: string;

  coefficient: number;

  method: string;

  direction?: string | null;
}


// ============================================================
// Outliers
// ============================================================

export interface OutlierFinding {
  column: string;

  count: number;

  percentage?: number | null;

  method?: string | null;

  lower_bound?: number | null;

  upper_bound?: number | null;
}


// ============================================================
// Temporal Analysis
// ============================================================

export interface TemporalFinding {
  date_column: string;

  minimum_date?: string | null;

  maximum_date?: string | null;

  time_span_days?: number | null;

  trend_direction?: string | null;

  period_values: Record<string, any>[];
}


// ============================================================
// Verified Analysis
// ============================================================

export interface ColumnInfoReport {
  name: string;
  dtype: string;
  unique: number;
  missing: number;
  missing_percentage?: number | null;
  memory_usage?: number | null;
}

export interface VerifiedAnalysisReport {
  dataset: DatasetReportInfo;
  data_quality: DataQualityReport;
  column_info: ColumnInfoReport[];
  statistics: DescriptiveStatistics[];
  correlations: CorrelationFinding[];
  outliers: OutlierFinding[];
  temporal_analysis: TemporalFinding[];
}

// ============================================================
// Professional Insights
// ============================================================

export type InsightPriority =
  | "Critical"
  | "High"
  | "Medium"
  | "Low";


export type InsightConfidence =
  | "High"
  | "Medium"
  | "Low";


export interface InsightEvidence {
  metric: string;

  value: string;

  context?: string | null;
}


export interface ProfessionalInsight {
  category: string;

  title: string;

  finding: string;

  evidence: InsightEvidence[];

  interpretation: string;

  potential_impact: string;

  recommended_action: string;

  priority: InsightPriority;

  confidence: InsightConfidence;
}


export interface InsightReport {
  insights: ProfessionalInsight[];

  top_findings: ProfessionalInsight[];

  top_actions: ProfessionalInsight[];
}


// ============================================================
// Complete Analysis Response
// ============================================================

export interface AnalysisData {
  analysis_id: number;

  created_at: string;

  verified_analysis: VerifiedAnalysisReport;

  insights: InsightReport;
}


// ============================================================
// Get Analysis
// ============================================================

export async function getAnalysis(
  datasetId: number
): Promise<AnalysisData> {

  const response =
    await api.get<AnalysisData>(
      `/analysis/${datasetId}`
    );

  return response.data;
}