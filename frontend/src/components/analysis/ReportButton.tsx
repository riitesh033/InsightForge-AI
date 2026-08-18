import { useState } from "react";
import {
  Download,
  Loader2,
} from "lucide-react";

import api from "@/lib/api";

interface Props {
  datasetId: number;
}

export default function ReportButton({
  datasetId,
}: Props) {
  const [loading, setLoading] = useState(false);

  async function downloadReport() {
    try {
      setLoading(true);

      const response = await api.get(
        `/analysis/${datasetId}/report`,
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
        `insightforge-analysis-${datasetId}.pdf`;

      document.body.appendChild(link);

      link.click();

      link.remove();

      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error(
        "Report download failed:",
        error
      );

      alert(
        "Failed to generate the report. Please try again."
      );

    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      type="button"
      onClick={downloadReport}
      disabled={loading}
      className="flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {loading ? (
        <>
          <Loader2 className="h-5 w-5 animate-spin" />
          Generating...
        </>
      ) : (
        <>
          <Download className="h-5 w-5" />
          Generate Report
        </>
      )}
    </button>
  );
}