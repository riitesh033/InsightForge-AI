import api from "@/lib/api";


// =========================
// Dashboard Stats
// =========================

export interface DashboardStats {
  total_datasets: number;
  total_analyses: number;
  average_quality_score: number;
  total_rows: number;
}


// =========================
// Recent Dataset
// =========================

export interface RecentDataset {
  id: number;
  filename: string;
  original_filename: string;
  rows: number;
  columns: number;
  uploaded_at: string;
  quality_score: number | null;
}


// =========================
// Recent Analysis
// =========================

export interface RecentAnalysis {
  analysis_id: number;
  dataset_id: number;
  dataset_name: string;
  quality_score: number;
  created_at: string;
}


// =========================
// Charts
// =========================

export interface UploadTrend {
  month: string;
  uploads: number;
}


export interface FileTypeDistribution {
  file_type: string;
  count: number;
}


export interface QualityDistribution {
  range: string;
  count: number;
}


export interface DashboardCharts {
  uploads_per_month: UploadTrend[];
  file_types: FileTypeDistribution[];
  quality_distribution: QualityDistribution[];
}


// =========================
// Dashboard Response
// =========================

export interface DashboardResponse {
  stats: DashboardStats;
  recent_datasets: RecentDataset[];
  recent_analyses: RecentAnalysis[];
  charts: DashboardCharts;
}


// =========================
// Get Dashboard
// =========================

export async function getDashboard() {

  const response =
    await api.get<DashboardResponse>(
      "/api/v1/dashboard"
    );

  return response.data;

}