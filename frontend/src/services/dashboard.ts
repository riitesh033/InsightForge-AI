import api from "@/lib/api";

export interface DashboardStats {
  total_datasets: number;
  total_analyses: number;
  average_quality_score: number;
  total_rows: number;
}

export interface RecentDataset {
  id: number;
  filename: string;
  original_filename: string;
  rows: number;
  columns: number;
  uploaded_at: string;
  quality_score: number | null;
}

export interface RecentAnalysis {
  analysis_id: number;
  dataset_id: number;
  dataset_name: string;
  quality_score: number;
  created_at: string;
}

export interface DashboardResponse {
  stats: DashboardStats;
  recent_datasets: RecentDataset[];
  recent_analyses: RecentAnalysis[];
}

export async function getDashboard() {
  const response = await api.get<DashboardResponse>("/dashboard");
  return response.data;
}