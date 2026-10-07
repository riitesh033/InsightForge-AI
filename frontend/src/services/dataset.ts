import { createClient } from "@supabase/supabase-js";
import api from "@/lib/api";

function getSupabaseConfig() {
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL?.trim();
  const supabaseAnonKey =
    import.meta.env.VITE_SUPABASE_ANON_KEY?.trim();
  const supabaseBucket = (
    import.meta.env.VITE_SUPABASE_BUCKET ?? "insightforge-files"
  )
    .trim()
    .replace(/\/+$/, "");

  return {
    supabaseUrl,
    supabaseAnonKey,
    supabaseBucket: supabaseBucket || "insightforge-files",
  };
}

function getSupabaseClient() {
  const { supabaseUrl, supabaseAnonKey } = getSupabaseConfig();

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "Supabase upload is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in the frontend environment."
    );
  }

  return createClient(supabaseUrl, supabaseAnonKey);
}

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

export type DownloadFormat =
  | "xlsx"
  | "csv"
  | "pdf"
  | "original";

export type DatasetFileFormat =
  | "csv"
  | "xlsx"
  | "xls";

// =========================
// Download Helpers
// =========================

function downloadBlob(
  blob: Blob,
  filename: string
): void {
  const url =
    window.URL.createObjectURL(blob);

  const link =
    document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.appendChild(link);

  link.click();

  link.remove();

  window.URL.revokeObjectURL(url);
}

function getDownloadFilename(
  contentDisposition: string | undefined,
  fallback: string
): string {
  const match =
    contentDisposition?.match(
      /filename="?([^";]+)"?/i
    );

  return match?.[1] ?? fallback;
}

// =========================
// Get Datasets
// =========================

export async function getDatasets(
  params: DatasetQuery = {}
): Promise<DatasetListResponse> {
  const response =
    await api.get<DatasetListResponse>(
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
  const response =
    await api.patch<Dataset>(
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
  await api.delete(
    `/datasets/${datasetId}`
  );
}

// =========================
// Upload Dataset
// =========================

export async function uploadDataset(
  file: File
): Promise<Dataset> {
  /*
   * Supabase Storage uses separate objects
   * for each dataset chunk.
   *
   * 40 MB keeps every individual object below
   * the configured Supabase Storage chunk limit.
   */
  const DEFAULT_CHUNK_SIZE =
    40 * 1024 * 1024;
  const supabase = getSupabaseClient();
  const { supabaseBucket } = getSupabaseConfig();

  // ---------------------------------
  // Step 1: Initialize upload
  // ---------------------------------

  const initResponse =
    await api.post<{
      storage_id: string;
      original_filename: string;
      file_type: string;
      file_size: number;
      chunk_size: number;
    }>(
      "/datasets/upload/init",
      {
        filename: file.name,
        file_size: file.size,
      }
    );

  const {
    storage_id,
    chunk_size,
  } = initResponse.data;

  const chunkSize =
    chunk_size > 0
      ? Math.min(
          chunk_size,
          DEFAULT_CHUNK_SIZE
        )
      : DEFAULT_CHUNK_SIZE;

  const totalChunks =
    Math.ceil(
      file.size / chunkSize
    );

  // ---------------------------------
  // Step 2: Upload chunks
  // ---------------------------------

  for (
    let chunkIndex = 0;
    chunkIndex < totalChunks;
    chunkIndex += 1
  ) {
    const start =
      chunkIndex * chunkSize;

    const end = Math.min(
      start + chunkSize,
      file.size
    );

    const chunk = file.slice(
      start,
      end
    );

    // Request a signed upload URL
    // for this specific chunk.
    const urlResponse =
      await api.post<{
        storage_id: string;
        chunk_index: number;
        path: string;
        token: string;
      }>(
        "/datasets/upload/chunk-url",
        null,
        {
          params: {
            storage_id,
            chunk_index:
              chunkIndex,
          },
        }
      );

    const {
      path,
      token,
    } = urlResponse.data;

    // Upload directly from the browser
    // to Supabase Storage.
    const {
      error,
    } =
      await supabase.storage
        .from(
          supabaseBucket
        )
        .uploadToSignedUrl(
          path,
          token,
          chunk
        );

    if (error) {
      throw new Error(
        `Failed to upload chunk ${
          chunkIndex + 1
        } of ${totalChunks}: ${
          error.message
        }`
      );
    }
  }

  // ---------------------------------
  // Step 3: Finalize upload
  // ---------------------------------

  /*
   * Tell the backend that all chunks have
   * been uploaded.
   *
   * The backend will:
   * 1. Create the Supabase manifest.
   * 2. Reconstruct the chunks temporarily.
   * 3. Analyze the dataset.
   * 4. Create the Dataset database record.
   * 5. Create the Analysis database record.
   * 6. Keep the original dataset in Supabase.
   * 7. Return the completed Dataset object.
   */
  const finalizeResponse =
    await api.post<Dataset>(
      "/datasets/upload/finalize",
      null,
      {
        params: {
          storage_id,
          original_filename:
            file.name,
          file_size:
            file.size,
          total_chunks:
            totalChunks,
        },
      }
    );

  return finalizeResponse.data;
}

// =========================
// Download Original Dataset
// =========================

export async function downloadDataset(
  datasetId: number,
  format: DatasetFileFormat
): Promise<void> {
  const response =
    await api.get(
      `/datasets/${datasetId}/download`,
      {
        responseType: "blob",
      }
    );

  downloadBlob(
    response.data,
    getDownloadFilename(
      response.headers[
        "content-disposition"
      ],
      `dataset_${datasetId}.${format}`
    )
  );
}

// =========================
// Download Original Dataset
// =========================

export async function downloadOriginalDataset(
  datasetId: number
): Promise<void> {
  const response =
    await api.get(
      `/datasets/${datasetId}/download`,
      {
        responseType: "blob",
      }
    );

  downloadBlob(
    response.data,
    getDownloadFilename(
      response.headers[
        "content-disposition"
      ],
      `dataset_${datasetId}_original`
    )
  );
}

// =========================
// Preview Cleaning
// =========================

export async function previewCleaning(
  datasetId: number
): Promise<CleaningResponse> {
  const response =
    await api.post<CleaningResponse>(
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
  const response =
    await api.post<CleaningResponse>(
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
  const response =
    await api.get(
      `/cleaning/${datasetId}/download`,
      {
        responseType: "blob",
      }
    );

  downloadBlob(
    response.data,
    getDownloadFilename(
      response.headers[
        "content-disposition"
      ],
      `dataset_${datasetId}_cleaned.${format}`
    )
  );
}

// =========================
// Download Analysis Report
// =========================

export async function downloadAnalysisReport(
  datasetId: number
): Promise<void> {
  const response =
    await api.get(
      `/reports/${datasetId}/pdf`,
      {
        responseType: "blob",
      }
    );

  const blob = new Blob(
    [response.data],
    {
      type: "application/pdf",
    }
  );

  const objectUrl =
    window.URL.createObjectURL(blob);

  const link =
    document.createElement("a");

  link.href = objectUrl;

  link.download =
    `dataset_${datasetId}_analysis_report.pdf`;

  document.body.appendChild(link);

  link.click();

  link.remove();

  window.URL.revokeObjectURL(
    objectUrl
  );
}

// =========================
// Unified Download
// =========================

export async function downloadDatasetFile(
  datasetId: number,
  format: DownloadFormat
): Promise<void> {
  if (format === "pdf") {
    await downloadAnalysisReport(
      datasetId
    );

    return;
  }

  if (format === "original") {
    await downloadOriginalDataset(
      datasetId
    );

    return;
  }

  await downloadCleanedDataset(
    datasetId,
    format
  );
}