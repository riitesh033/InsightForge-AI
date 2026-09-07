import {
  UploadCloud,
  FileSpreadsheet,
  Info,
  Trash2,
  CheckCircle2,
} from "lucide-react";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { showError, showSuccess } from "@/lib/toast";
import { uploadDataset } from "@/services/dataset";

export default function UploadDatasetPage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  // =========================
  // File Validation
  // =========================

  function validateFile(file: File): boolean {
    const extension = file.name.split(".").pop()?.toLowerCase();

    if (!extension || !["csv", "xls", "xlsx"].includes(extension)) {
      showError("Only CSV, XLS and XLSX files are supported.");
      return false;
    }

    if (file.size > 20 * 1024 * 1024) {
      showError("Maximum file size is 20 MB.");
      return false;
    }

    return true;
  }

  // =========================
  // Select File
  // =========================

  function handleFile(file: File) {
    if (!validateFile(file)) {
      return;
    }

    setSelectedFile(file);
    setProgress(0);
  }

  // =========================
  // File Input
  // =========================

  function handleFileChange(
    e: React.ChangeEvent<HTMLInputElement>
  ) {
    const file = e.target.files?.[0];

    if (!file) {
      return;
    }

    handleFile(file);

    // Allow selecting the same file again
    e.target.value = "";
  }

  // =========================
  // Drag & Drop
  // =========================

  function handleDragEnter(
    e: React.DragEvent<HTMLDivElement>
  ) {
    e.preventDefault();
    e.stopPropagation();

    setDragging(true);
  }

  function handleDragOver(
    e: React.DragEvent<HTMLDivElement>
  ) {
    e.preventDefault();
    e.stopPropagation();

    e.dataTransfer.dropEffect = "copy";

    if (!dragging) {
      setDragging(true);
    }
  }

  function handleDragLeave(
    e: React.DragEvent<HTMLDivElement>
  ) {
    e.preventDefault();
    e.stopPropagation();

    if (
      e.currentTarget.contains(
        e.relatedTarget as Node
      )
    ) {
      return;
    }

    setDragging(false);
  }

  function handleDrop(
    e: React.DragEvent<HTMLDivElement>
  ) {
    e.preventDefault();
    e.stopPropagation();

    setDragging(false);

    const files = e.dataTransfer.files;

    if (!files || files.length === 0) {
      return;
    }

    handleFile(files[0]);
  }

  // =========================
  // Upload
  // =========================

  async function handleUpload() {
    if (!selectedFile) {
      showError("Please select a dataset first.");
      return;
    }

    try {
      setUploading(true);
      setProgress(0);

      const response = await uploadDataset(selectedFile);

      console.log("UPLOAD RESPONSE:", response);

      showSuccess(
        "Dataset uploaded successfully."
      );

      setProgress(100);

      setTimeout(() => {
        navigate("/dashboard/datasets");
      }, 1000);
    } catch (error: any) {
      console.error(
        "Dataset upload failed:",
        error
      );

      const message =
        error?.response?.data?.detail ??
        error?.message ??
        "Upload failed. Please try again.";

      showError(message);
    } finally {
      setUploading(false);
    }
  }

  // =========================
  // Remove Selected File
  // =========================

  function removeSelectedFile() {
    if (uploading) {
      return;
    }

    setSelectedFile(null);
    setProgress(0);
  }

  // =========================
  // Format File Size
  // =========================

  function formatFileSize(size: number) {
    if (size < 1024) {
      return `${size} B`;
    }

    if (size < 1024 * 1024) {
      return `${(size / 1024).toFixed(2)} KB`;
    }

    return `${(size / (1024 * 1024)).toFixed(2)} MB`;
  }

  return (
    <div className="space-y-8">
      {/* =========================
          Page Header
      ========================== */}

      <div>
        <h1 className="text-3xl font-bold">
          Upload Dataset
        </h1>

        <p className="mt-2 text-muted-foreground">
          Upload CSV or Excel datasets for
          AI-powered analysis.
        </p>
      </div>

      {/* =========================
          Hidden File Input
      ========================== */}

      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xls,.xlsx"
        className="hidden"
        onChange={handleFileChange}
        disabled={uploading}
      />

      {/* =========================
          Upload Area
      ========================== */}

      <div className="rounded-xl border bg-card p-8 shadow-sm">
        <div
          onClick={() =>
            !uploading &&
            inputRef.current?.click()
          }
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`flex min-h-[320px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-16 text-center transition-all duration-300 ${
            dragging
              ? "scale-[1.02] border-primary bg-primary/10"
              : "border-border hover:border-primary hover:bg-accent/40"
          } ${
            uploading
              ? "cursor-not-allowed opacity-60"
              : ""
          }`}
        >
          <div className="rounded-2xl bg-primary/10 p-5">
            <UploadCloud
              size={56}
              className="text-primary"
            />
          </div>

          <h2 className="mt-6 text-2xl font-semibold">
            Drag & Drop Dataset
          </h2>

          <p className="mt-3 text-muted-foreground">
            or click to browse files
          </p>

          <p className="mt-2 text-sm text-muted-foreground">
            CSV • XLS • XLSX • Maximum 20 MB
          </p>
        </div>
      </div>

      {/* =========================
          Selected File
      ========================== */}

      {selectedFile && (
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center">
            {/* File Icon */}

            <div className="flex shrink-0 items-center justify-center rounded-lg bg-primary/10 p-3">
              <FileSpreadsheet
                size={30}
                className="text-primary"
              />
            </div>

            {/* File Information */}

            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h3 className="break-all font-semibold">
                  {selectedFile.name}
                </h3>

                {!uploading &&
                  progress === 100 && (
                    <CheckCircle2
                      size={18}
                      className="shrink-0 text-green-500"
                    />
                  )}
              </div>

              <p className="mt-1 text-sm text-muted-foreground">
                {formatFileSize(
                  selectedFile.size
                )}
              </p>

              {/* Upload Progress */}

              {uploading && (
                <div className="mt-4">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>
                      Uploading dataset...
                    </span>

                    <span>
                      {progress}%
                    </span>
                  </div>

                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-all duration-300"
                      style={{
                        width: `${progress}%`,
                      }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}

            <div className="flex shrink-0 items-center gap-3">
              <button
                type="button"
                disabled={uploading}
                onClick={removeSelectedFile}
                title="Remove file"
                className="rounded-lg p-2 text-red-500 transition hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Trash2 size={20} />
              </button>

              <button
                type="button"
                disabled={
                  uploading || !selectedFile
                }
                onClick={handleUpload}
                className="rounded-lg bg-primary px-6 py-2.5 font-medium text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {uploading
                  ? `Uploading ${progress}%`
                  : "Upload Dataset"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =========================
          Processing Information
      ========================== */}

      <div className="rounded-xl border bg-card p-6 shadow-sm">
        <div className="flex items-start gap-3">
          <Info
            size={22}
            className="mt-1 shrink-0 text-primary"
          />

          <div>
            <h3 className="font-semibold">
              What happens after uploading?
            </h3>

            <ul className="mt-4 list-disc space-y-2 pl-5 text-muted-foreground">
              <li>
                Dataset validation
              </li>

              <li>
                Missing value detection
              </li>

              <li>
                Duplicate row detection
              </li>

              <li>
                Outlier detection
              </li>

              <li>
                Automatic statistical profiling
              </li>

              <li>
                Correlation analysis
              </li>

              <li>
                AI-generated business insights
              </li>

              <li>
                Interactive dashboard generation
              </li>

              <li>
                Professional analysis report
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}