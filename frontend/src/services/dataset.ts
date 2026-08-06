import api from "@/lib/api";

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

export interface DatasetListResponse {
  items: Dataset[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DatasetQuery {
  page?: number;
  page_size?: number;
  search?: string;
  sort_by?: string;
  order?: "asc" | "desc";
}

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

export async function deleteDataset(datasetId: number) {
  return api.delete(`/datasets/${datasetId}`);
}

export function downloadDataset(
  datasetId: number
) {
  const apiUrl = import.meta.env.VITE_API_URL;

  window.open(
    `${apiUrl}/datasets/${datasetId}/download`,
    "_blank"
  );
}