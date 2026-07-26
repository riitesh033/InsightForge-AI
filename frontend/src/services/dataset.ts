import api from "./api";

export interface Dataset {
  id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  file_path: string;
  rows: number;
  columns: number;
  uploaded_at: string;
  owner_id: number;
}

export async function uploadDataset(
  file: File,
  onProgress?: (progress: number) => void
) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await api.post(
    "/api/v1/datasets/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },

      onUploadProgress: (event) => {
        if (!event.total || !onProgress) return;

        onProgress(
          Math.round(
            (event.loaded * 100) /
            event.total
          )
        );
      },
    }
  );

  return response.data as Dataset;
}

export async function getDatasets() {
  const response = await api.get(
    "/api/v1/datasets"
  );

  return response.data as Dataset[];
}

export async function getDataset(
  id: number
) {
  const response = await api.get(
    `/api/v1/datasets/${id}`
  );

  return response.data as Dataset;
}

export async function renameDataset(
  id: number,
  name: string
) {
  const response = await api.patch(
    `/api/v1/datasets/${id}`,
    {
      name,
    }
  );

  return response.data as Dataset;
}

export async function deleteDataset(
  id: number
) {
  await api.delete(
    `/api/v1/datasets/${id}`
  );
}

export function downloadDataset(
  id: number
) {
  window.open(
    `http://localhost:8000/api/v1/datasets/${id}/download`,
    "_blank"
  );
}