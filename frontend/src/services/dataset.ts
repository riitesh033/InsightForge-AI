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
          Math.round((event.loaded * 100) / event.total)
        );
      },
    }
  );

  return response.data as Dataset;
}

export async function getDatasets() {
  const response = await api.get("/api/v1/datasets");

  return response.data as Dataset[];
}

export async function getDataset(id: number) {
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
      original_filename: name,
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

export async function downloadDataset(
  id: number
) {
  try {
    const response = await api.get(
      `/api/v1/datasets/${id}/download`,
      {
        responseType: "blob",
      }
    );

    const blob = new Blob([response.data]);

    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");

    const disposition =
      response.headers["content-disposition"];

    let filename = "dataset";

    if (disposition) {
      const match = disposition.match(
        /filename="?([^"]+)"?/
      );

      if (match) {
        filename = match[1];
      }
    }

    link.href = url;
    link.download = filename;

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error(error);
    alert("Failed to download dataset.");
  }
}