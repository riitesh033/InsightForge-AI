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
// Get Datasets
// =========================

export async function getDatasets(
  params: DatasetQuery = {}
): Promise<DatasetListResponse> {
  const response = await api.get<DatasetListResponse>(
    "/datasets",
    {
      params,
    }
  );

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
// Download Original Dataset
// =========================

export async function downloadDataset(
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
  link.setAttribute("download", "dataset");

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
  datasetId: number
): Promise<void> {
  const response = await api.get(
    `/cleaning/${datasetId}/download`,
    {
      responseType: "blob",
    }
  );

  const blob = new Blob([response.data]);

  const url = window.URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = url;

  // The backend sends the correct file through FileResponse.
  // This filename is only a fallback.
  link.setAttribute(
    "download",
    "cleaned_dataset"
  );

  document.body.appendChild(link);

  link.click();

  link.remove();

  window.URL.revokeObjectURL(url);
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
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
}