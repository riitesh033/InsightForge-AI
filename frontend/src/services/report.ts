import api from "@/lib/api";

export interface Report {
  dataset_id: number;
  dataset_name: string;
  uploaded_at: string;
  analysis_id: number;
  quality_score: number;
}

export async function getReports(): Promise<Report[]> {
  const response = await api.get<Report[]>("/reports");
  return response.data;
}

export async function downloadReport(
  datasetId: number
): Promise<Blob> {
  const response = await api.get(
    `/reports/${datasetId}/pdf`,
    {
      responseType: "blob",
    }
  );

  return response.data;
}

export function savePdf(
  blob: Blob,
  filename: string
): void {
  const url = window.URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.appendChild(link);
  link.click();

  link.remove();

  window.URL.revokeObjectURL(url);
}