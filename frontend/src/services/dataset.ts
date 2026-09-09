import api from "@/lib/api";

// =========================
// Dataset
// =========================

export interface Dataset {
  id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  rows: number;
  columns: number;
  uploaded_at: string;
  owner_id: number;
  file_path: string;
  cleaned_available: boolean;
  cleaned_filename: string | null;
}

// =========================
// Dataset Query
// =========================

export interface DatasetQuery {
  page?: number;
  page_size?: number;
  search?: string;
  sort_by?: string;
  order?: "asc" | "desc";
}

// =========================
// Dataset List Response
// =========================

export interface DatasetListResponse {
  items: Dataset[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// =========================
// Cleaning
// =========================

export interface CleaningChange {
  column: string | null;
  action: string;
  count: number;
  replacement_value?: string | number;
}

export interface CleaningPreview {
  rows_before: number;
  rows_after: number;
  columns: number;

  empty_strings_replaced: number;
  whitespace_cleaned: number;

  missing_values_before: number;
  missing_values_after: number;
  missing_values_filled: number;

  duplicates_removed: number;

  outliers_detected: Record<string, number>;

  changes: CleaningChange[];

  warnings: string[];

  cleaned_filename?: string;
  cleaned_file_path?: string;
}

export interface CleaningResponse {
  dataset_id: number;
  original_filename: string;
  cleaned_filename: string | null;
  download_available: boolean;
  preview: CleaningPreview;
}

// =========================
// Download Format
// =========================

export type DownloadFormat = "xlsx" | "csv" | "pdf" | "original";

// =========================
// Get Datasets
// =========================

export async function getDatasets(
  params: DatasetQuery = {}
): Promise<DatasetListResponse> {
  const response = await api.get<DatasetListResponse>("/datasets", {
    params,
  });

  return response.data;
}

// =========================
// Rename Dataset
// =========================

export async function renameDataset(
  datasetId: number,
  original_filename: string
): Promise<Dataset> {
  const response = await api.patch<Dataset>(
    `/datasets/${datasetId}`,
    {
      original_filename,
    }
  );

  return response.data;
}

// =========================
// Delete Dataset
// =========================

export async function deleteDataset(
  datasetId: number
): Promise<void> {
  await api.delete(`/datasets/${datasetId}`);
}

// =========================
// Upload Dataset
// =========================

export async function uploadDataset(
  file: File
): Promise<Dataset> {
  const formData = new FormData();

  formData.append("file", file);

  const response = await api.post<Dataset>(
    "/datasets/upload",
    formData
  );

  return response.data;
}

// =========================
// Download Original Dataset
// =========================

export async function downloadDataset(
  datasetId: number,
  format: DownloadFormat
): Promise<void> {
  const response = await api.get(
    `/datasets/${datasetId}/download`,
    {
      responseType: "blob",
      params: {
        format,
      },
    }
  );

  const blob = new Blob([response.data]);

  const url = window.URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = url;
  link.download = `dataset_${datasetId}.${format}`;

  document.body.appendChild(link);

  link.click();

  link.remove();

  window.URL.revokeObjectURL(url);
}

// =========================
// Download Original Dataset (Simple)
// =========================

export async function downloadOriginalDataset(
  datasetId: number
): Promise<void> {
  const response = await api.get(
    `/datasets/${datasetId}/download`,
    {
      responseType: "blob",
    }
  );

  const blob = new Blob([response.data]);

  const url = window.URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = url;
  link.download = `dataset_${datasetId}_original`;

  document.body.appendChild(link);

  link.click();

  link.remove();

  window.URL.revokeObjectURL(url);
}

// =========================
// Preview Cleaning
// =========================

export async function previewCleaning(
  datasetId: number
): Promise<CleaningResponse> {
  const response = await api.post<CleaningResponse>(
    `/cleaning/${datasetId}/preview`
  );

  return response.data;
}

// =========================
// Apply Cleaning
// =========================

export async function applyCleaning(
  datasetId: number
): Promise<CleaningResponse> {
  const response = await api.post<CleaningResponse>(
    `/cleaning/${datasetId}/apply`
  );

  return response.data;
}

// =========================
// Download Cleaned Dataset
// =========================

export async function downloadCleanedDataset(
  datasetId: number,
  format: "xlsx" | "csv"
): Promise<void> {
  const response = await api.get(
    `/cleaning/${datasetId}/download`,
    {
      responseType: "blob",
      params: {
        format,
      },
    }
  );

  const blob = new Blob([response.data]);

  const objectUrl = window.URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = objectUrl;
  link.download = `dataset_${datasetId}_cleaned.${format}`;

  document.body.appendChild(link);

  link.click();

  link.remove();

  window.URL.revokeObjectURL(objectUrl);
}

// =========================
// Download Analysis Report
// =========================

export async function downloadAnalysisReport(
  datasetId: number
): Promise<void> {
  const response = await api.get(
    `/reports/${datasetId}/pdf`,
    {
      responseType: "blob",
    }
  );

  const blob = new Blob([response.data], {
    type: "application/pdf",
  });

  const objectUrl = window.URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = objectUrl;
  link.download = `dataset_${datasetId}_analysis_report.pdf`;

  document.body.appendChild(link);

  link.click();

  link.remove();

  window.URL.revokeObjectURL(objectUrl);
}

// =========================
// Unified Download
// =========================

export async function downloadDatasetFile(
  datasetId: number,
  format: DownloadFormat
): Promise<void> {
  if (format === "pdf") {
    await downloadAnalysisReport(datasetId);
    return;
  }

  if (format === "original") {
    await downloadOriginalDataset(datasetId);
    return;
  }

  await downloadCleanedDataset(datasetId, format);
}

