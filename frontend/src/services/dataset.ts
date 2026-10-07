import axios from "axios";

import api from "@/lib/api";

function getSupabaseConfig() {
  const supabaseUrl =
    import.meta.env.VITE_SUPABASE_URL?.trim();

  const supabaseAnonKey =
    import.meta.env.VITE_SUPABASE_ANON_KEY?.trim();

  const supabaseBucket = (
    import.meta.env.VITE_SUPABASE_BUCKET ??
    "insightforge-files"
  )
    .trim()
    .replace(/\/+$/, "");

  return {
    supabaseUrl,
    supabaseAnonKey,
    supabaseBucket:
      supabaseBucket || "insightforge-files",
  };
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

export type DatasetUploadProgress =
  (progress: number) => void;

/**
 * Fallback upload through the regular backend
 * multipart endpoint.
 */
async function uploadDatasetMultipart(
  file: File,
  onProgress?: DatasetUploadProgress
): Promise<Dataset> {
  const formData = new FormData();

  formData.append("file", file);

  const response =
    await api.post<Dataset>(
      "/datasets/upload",
      formData,
      {
        onUploadProgress: (event) => {
          if (!event.total) {
            return;
          }

          const progress = Math.min(
            95,
            Math.round(
              (event.loaded / event.total) * 95
            )
          );

          onProgress?.(progress);
        },
      }
    );

  return response.data;
}

/**
 * Upload one chunk directly to Supabase
 * using the signed URL returned by the backend.
 *
 * Axios provides browser upload progress events,
 * allowing the UI to display real upload progress.
 */
async function uploadSignedChunk(
  signedUrl: string,
  chunk: Blob,
  onProgress: (loaded: number) => void
): Promise<void> {
  const formData = new FormData();

  formData.append(
    "cacheControl",
    "3600"
  );

  formData.append(
    "",
    chunk
  );

  await axios.put(
    signedUrl,
    formData,
    {
      headers: {
        "x-upsert": "false",
      },

      onUploadProgress: (event) => {
        const loaded =
          event.total
            ? Math.round(
                (event.loaded / event.total) *
                  chunk.size
              )
            : event.loaded;

        onProgress(
          Math.min(
            chunk.size,
            loaded
          )
        );
      },
    }
  );
}

/**
 * Upload dataset using chunked Supabase storage.
 *
 * Large files are divided into chunks and two
 * chunks are uploaded concurrently.
 *
 * Progress:
 *
 * 0-95%  = actual browser upload progress
 * 95-100% = backend finalization/processing
 */
export async function uploadDataset(
  file: File,
  onProgress?: DatasetUploadProgress
): Promise<Dataset> {
  const DEFAULT_CHUNK_SIZE =
    40 * 1024 * 1024;

  const UPLOAD_CONCURRENCY = 2;

  const {
    supabaseUrl,
    supabaseAnonKey,
  } = getSupabaseConfig();

  // -------------------------------------------------
  // Fallback to normal backend multipart upload
  // -------------------------------------------------

  if (
    !supabaseUrl ||
    !supabaseAnonKey
  ) {
    return uploadDatasetMultipart(
      file,
      onProgress
    );
  }

  // -------------------------------------------------
  // Step 1: Initialize upload
  // -------------------------------------------------

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
      ? chunk_size
      : DEFAULT_CHUNK_SIZE;

  const totalChunks =
    Math.ceil(
      file.size / chunkSize
    );

  // Track uploaded bytes for every chunk.
  const uploadedBytes =
    new Array<number>(
      totalChunks
    ).fill(0);

  // -------------------------------------------------
  // Calculate combined upload progress
  // -------------------------------------------------

  const updateProgress = () => {
    const totalUploaded =
      uploadedBytes.reduce(
        (sum, bytes) =>
          sum + bytes,
        0
      );

    const progress =
      Math.floor(
        (totalUploaded / file.size) *
          95
      );

    onProgress?.(
      Math.min(
        95,
        progress
      )
    );
  };

  // -------------------------------------------------
  // Upload one chunk
  // -------------------------------------------------

  const uploadChunk = async (
    chunkIndex: number
  ): Promise<void> => {
    const start =
      chunkIndex * chunkSize;

    const end =
      Math.min(
        start + chunkSize,
        file.size
      );

    const chunk =
      file.slice(
        start,
        end
      );

    // Request a signed URL for this chunk.
    const urlResponse =
      await api.post<{
        storage_id: string;
        chunk_index: number;
        path: string;
        token: string;
        signed_url: string;
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
      signed_url,
    } = urlResponse.data;

    if (!signed_url) {
      throw new Error(
        `Server did not return a signed upload URL for chunk ${
          chunkIndex + 1
        } of ${totalChunks}.`
      );
    }

    // Upload directly to Supabase
    // and update global progress.
    await uploadSignedChunk(
      signed_url,
      chunk,
      (loaded) => {
        uploadedBytes[
          chunkIndex
        ] = loaded;

        updateProgress();
      }
    );

    // Ensure this chunk is marked complete.
    uploadedBytes[
      chunkIndex
    ] = chunk.size;

    updateProgress();
  };

  // -------------------------------------------------
  // Step 2: Upload chunks concurrently
  // -------------------------------------------------

  for (
    let batchStart = 0;
    batchStart < totalChunks;
    batchStart +=
      UPLOAD_CONCURRENCY
  ) {
    const batchEnd =
      Math.min(
        batchStart +
          UPLOAD_CONCURRENCY,
        totalChunks
      );

    await Promise.all(
      Array.from(
        {
          length:
            batchEnd -
            batchStart,
        },
        (_, offset) =>
          uploadChunk(
            batchStart +
              offset
          )
      )
    );
  }

  // -------------------------------------------------
  // Step 3: Upload finished
  // -------------------------------------------------

  onProgress?.(95);

  // -------------------------------------------------
  // Step 4: Finalize upload
  // -------------------------------------------------

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

  // Everything has completed.
  onProgress?.(100);

  return finalizeResponse.data;
}

// =========================
// Download Dataset
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

  const blob =
    new Blob(
      [response.data],
      {
        type: "application/pdf",
      }
    );

  const objectUrl =
    window.URL.createObjectURL(
      blob
    );

  const link =
    document.createElement("a");

  link.href = objectUrl;

  link.download =
    `dataset_${datasetId}_analysis_report.pdf`;

  document.body.appendChild(
    link
  );

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