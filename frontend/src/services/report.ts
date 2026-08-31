import api from "@/lib/api";


// ============================================================
// Download PDF Report
// ============================================================

export async function downloadReport(
  datasetId: number
): Promise<void> {

  const response = await api.get(
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

  const url =
    window.URL.createObjectURL(blob);

  const link =
    document.createElement("a");

  link.href = url;

  link.download =
    `dataset_${datasetId}_analysis_report.pdf`;

  document.body.appendChild(link);

  link.click();

  link.remove();

  window.URL.revokeObjectURL(url);
}