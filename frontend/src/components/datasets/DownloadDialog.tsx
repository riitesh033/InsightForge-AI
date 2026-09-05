import { useState } from "react";
import { Download, FileSpreadsheet, FileText } from "lucide-react";

import {
  downloadDataset,
  DownloadFormat,
} from "@/services/dataset";

interface DownloadDialogProps {
  datasetId: number;
  cleanedAvailable: boolean;
}

export default function DownloadDialog({
  datasetId,
  cleanedAvailable,
}: DownloadDialogProps) {
  const [format, setFormat] =
    useState<DownloadFormat>("xlsx");

  const [downloading, setDownloading] = useState(false);

  async function handleDownload() {
    try {
      setDownloading(true);

      await downloadDataset(
        datasetId,
        format
      );
    } catch (error) {
      console.error(
        "Download failed:",
        error
      );
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="rounded-xl border border-stone-200 bg-white p-5 shadow-sm dark:border-stone-700 dark:bg-stone-900">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-stone-900 dark:text-stone-100">
          Download
        </h3>

        <p className="mt-1 text-sm text-stone-500">
          Choose what you want to download.
        </p>
      </div>

      <div className="space-y-3">

        {/* Excel */}
        <label
          className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 ${
            format === "xlsx"
              ? "border-stone-900 bg-stone-50 dark:border-stone-300 dark:bg-stone-800"
              : "border-stone-200 dark:border-stone-700"
          }`}
        >
          <input
            type="radio"
            name="download-format"
            value="xlsx"
            checked={format === "xlsx"}
            onChange={() => setFormat("xlsx")}
          />

          <FileSpreadsheet size={18} />

          <div>
            <div className="font-medium">
              Excel (.xlsx)
            </div>

            <div className="text-xs text-stone-500">
              Cleaned dataset
            </div>
          </div>
        </label>

        {/* CSV */}
        <label
          className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 ${
            format === "csv"
              ? "border-stone-900 bg-stone-50 dark:border-stone-300 dark:bg-stone-800"
              : "border-stone-200 dark:border-stone-700"
          }`}
        >
          <input
            type="radio"
            name="download-format"
            value="csv"
            checked={format === "csv"}
            onChange={() => setFormat("csv")}
          />

          <FileText size={18} />

          <div>
            <div className="font-medium">
              CSV (.csv)
            </div>

            <div className="text-xs text-stone-500">
              Cleaned dataset
            </div>
          </div>
        </label>

        {/* PDF */}
        <label
          className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 ${
            format === "pdf"
              ? "border-stone-900 bg-stone-50 dark:border-stone-300 dark:bg-stone-800"
              : "border-stone-200 dark:border-stone-700"
          }`}
        >
          <input
            type="radio"
            name="download-format"
            value="pdf"
            checked={format === "pdf"}
            onChange={() => setFormat("pdf")}
          />

          <FileText size={18} />

          <div>
            <div className="font-medium">
              PDF Report (.pdf)
            </div>

            <div className="text-xs text-stone-500">
              Professional analysis report
            </div>
          </div>
        </label>

      </div>

      <button
        onClick={handleDownload}
        disabled={
          downloading ||
          (format !== "pdf" && !cleanedAvailable)
        }
        className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-stone-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Download size={17} />

        {downloading
          ? "Downloading..."
          : format === "pdf"
            ? "Download Report"
            : cleanedAvailable
              ? "Download Cleaned Dataset"
              : "Apply Cleaning First"}
      </button>
    </div>
  );
}