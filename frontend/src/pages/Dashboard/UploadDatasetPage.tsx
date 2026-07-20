import {
  UploadCloud,
  FileSpreadsheet,
  Info,
  Trash2,
} from "lucide-react";
import { useState } from "react";

import { showError, showSuccess } from "@/lib/toast";
import { uploadDataset } from "@/services/dataset";

export default function UploadDatasetPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  function validateFile(file: File) {
    const allowedTypes = [
      "text/csv",
      "application/vnd.ms-excel",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ];

    const maxSize = 20 * 1024 * 1024;

    if (!allowedTypes.includes(file.type)) {
      showError("Only CSV and Excel files are supported.");
      return false;
    }

    if (file.size > maxSize) {
      showError("Maximum file size is 20 MB.");
      return false;
    }

    return true;
  }

  function handleFile(file: File) {
    if (!validateFile(file)) return;

    setSelectedFile(file);
  }

  function handleFileChange(
    e: React.ChangeEvent<HTMLInputElement>
  ) {
    if (!e.target.files?.length) return;

    handleFile(e.target.files[0]);
  }

  function handleDrop(
    e: React.DragEvent<HTMLLabelElement>
  ) {
    e.preventDefault();

    setDragging(false);

    if (!e.dataTransfer.files.length) return;

    handleFile(e.dataTransfer.files[0]);
  }

  async function handleUpload() {
    if (!selectedFile) {
      showError("Please select a dataset first.");
      return;
    }

    try {
      setUploading(true);
      setProgress(0);

      await uploadDataset(selectedFile, (progress) => {
        setProgress(progress);
      });

      showSuccess("Dataset uploaded successfully.");

      setSelectedFile(null);
      setProgress(0);
    } catch (error: any) {
      console.error(error);

      showError(
        error?.response?.data?.detail ??
          "Upload failed."
      );
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}

      <div>
        <h1 className="text-3xl font-bold text-foreground">
          Upload Dataset
        </h1>

        <p className="mt-2 text-muted-foreground">
          Upload CSV or Excel datasets for AI-powered analysis.
        </p>
      </div>

      {/* Upload Area */}

      <div className="rounded-xl border border-border bg-card p-8 shadow-sm">
        <label
          htmlFor="dataset"
          onDrop={handleDrop}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-16 transition ${
            dragging
              ? "border-primary bg-primary/5"
              : "border-border hover:border-primary hover:bg-accent/30"
          }`}
        >
          <UploadCloud
            size={60}
            className="text-primary"
          />

          <h2 className="mt-6 text-2xl font-semibold text-foreground">
            Drag & Drop Dataset
          </h2>

          <p className="mt-3 text-center text-muted-foreground">
            or click here to browse files
          </p>

          <p className="mt-2 text-sm text-muted-foreground">
            CSV • XLS • XLSX • Max 20 MB
          </p>

          <input
            id="dataset"
            type="file"
            accept=".csv,.xls,.xlsx"
            className="hidden"
            onChange={handleFileChange}
          />
        </label>
      </div>

      {/* Selected File */}

      {selectedFile && (
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center">
            <div className="rounded-lg bg-primary/10 p-3">
              <FileSpreadsheet
                size={28}
                className="text-primary"
              />
            </div>

            <div className="flex-1">
              <h3 className="font-semibold text-foreground break-all">
                {selectedFile.name}
              </h3>

              <p className="text-sm text-muted-foreground">
                {(selectedFile.size / 1024).toFixed(2)} KB
              </p>

              {uploading && (
                <div className="mt-4">
                  <div className="h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-all duration-300"
                      style={{
                        width: `${progress}%`,
                      }}
                    />
                  </div>

                  <p className="mt-2 text-xs text-muted-foreground">
                    {progress}% Uploaded
                  </p>
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setSelectedFile(null)}
                disabled={uploading}
                className="rounded-lg p-2 text-red-500 transition hover:bg-red-100 dark:hover:bg-red-900/30 disabled:opacity-50"
              >
                <Trash2 size={20} />
              </button>

              <button
                onClick={handleUpload}
                disabled={uploading}
                className="rounded-lg bg-primary px-5 py-2 font-medium text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {uploading ? "Uploading..." : "Upload"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Information */}

      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-start gap-3">
          <Info
            size={22}
            className="mt-1 text-primary"
          />

          <div>
            <h3 className="font-semibold text-foreground">
              What happens after uploading?
            </h3>

            <ul className="mt-4 list-disc space-y-2 pl-5 text-muted-foreground">
              <li>Dataset validation</li>
              <li>Missing value detection</li>
              <li>Duplicate row detection</li>
              <li>Outlier detection</li>
              <li>Automatic statistical profiling</li>
              <li>Correlation analysis</li>
              <li>AI-generated business insights</li>
              <li>Interactive dashboard generation</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}