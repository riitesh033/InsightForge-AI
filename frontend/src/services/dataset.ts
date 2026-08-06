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



export async function deleteDataset(
  datasetId: number
) {

  return api.delete(
    `/datasets/${datasetId}`
  );

}



export async function downloadDataset(
  datasetId: number
) {

  const response = await api.get(
    `/datasets/${datasetId}/download`,
    {
      responseType: "blob",
    }
  );


  const blob = new Blob(
    [response.data]
  );


  const url = window.URL.createObjectURL(
    blob
  );


  const link = document.createElement(
    "a"
  );


  link.href = url;


  link.setAttribute(
    "download",
    "dataset"
  );


  document.body.appendChild(
    link
  );


  link.click();


  link.remove();


  window.URL.revokeObjectURL(
    url
  );
}




export async function uploadDataset(
  file: File
) {

  const formData = new FormData();


  formData.append(
    "file",
    file
  );


  const response = await api.post(
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