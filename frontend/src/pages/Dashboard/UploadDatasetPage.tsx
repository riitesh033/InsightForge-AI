import {
  UploadCloud,
  FileSpreadsheet,
  Info,
  Trash2,
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

  function validateFile(file: File) {
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

  function handleFile(file: File) {
    if (!validateFile(file)) return;

    setSelectedFile(file);
  }

  function handleFileChange(
    e: React.ChangeEvent<HTMLInputElement>
  ) {
    const file = e.target.files?.[0];

    if (!file) return;

    handleFile(file);

    e.target.value = "";
  }

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

    if (e.currentTarget.contains(e.relatedTarget as Node)) {
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

async function handleUpload() {
  if (!selectedFile) {
    showError("Please select a dataset first.");
    return;
  }

  try {
    setUploading(true);
    setProgress(0);

    const response = await uploadDataset(
      selectedFile,
      (value) => {
        setProgress(value);
      }
    );

    console.log("UPLOAD RESPONSE:");
    console.log(response);

    showSuccess("Dataset uploaded successfully.");

    setTimeout(() => {
      navigate("/dashboard/datasets");
    }, 1000);
  } catch (error: any) {
    console.log("FULL ERROR:");
    console.log(error);

    console.log("ERROR RESPONSE:");
    console.log(error?.response);

    console.log("ERROR DATA:");
    console.log(error?.response?.data);

    showError(
      error?.response?.data?.detail ??
      error?.message ??
      "Upload failed."
    );
  } finally {
    setUploading(false);
  }
}

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">
          Upload Dataset
        </h1>

        <p className="mt-2 text-muted-foreground">
          Upload CSV or Excel datasets for AI-powered analysis.
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xls,.xlsx"
        className="hidden"
        onChange={handleFileChange}
      />

      <div className="rounded-xl border bg-card p-8 shadow-sm">
        <div
          onClick={() => inputRef.current?.click()}
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-16 transition-all duration-300 ${
            dragging
              ? "border-primary bg-primary/10 scale-[1.02]"
              : "border-border hover:border-primary hover:bg-accent/40"
          }`}
        >
          <UploadCloud
            size={60}
            className="text-primary"
          />

          <h2 className="mt-6 text-2xl font-semibold">
            Drag & Drop Dataset
          </h2>

          <p className="mt-3 text-muted-foreground">
            or click to browse files
          </p>

          <p className="mt-2 text-sm text-muted-foreground">
            CSV • XLS • XLSX • Max 20 MB
          </p>
        </div>
      </div>

      {selectedFile && (
        <div className="rounded-xl border bg-card p-6">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center">
            <div className="rounded-lg bg-primary/10 p-3">
              <FileSpreadsheet
                size={28}
                className="text-primary"
              />
            </div>

            <div className="flex-1">
              <h3 className="break-all font-semibold">
                {selectedFile.name}
              </h3>

              <p className="text-sm text-muted-foreground">
                {(selectedFile.size / 1024).toFixed(2)} KB
              </p>

              {uploading && (
                <div className="mt-4">
                  <div className="h-2 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-300"
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
                type="button"
                disabled={uploading}
                onClick={() => setSelectedFile(null)}
                className="rounded-lg p-2 text-red-500 hover:bg-red-500/10"
              >
                <Trash2 size={20} />
              </button>

              <button
                type="button"
                disabled={uploading}
                onClick={handleUpload}
                className="rounded-lg bg-primary px-5 py-2 font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
              >
                {uploading
                  ? "Uploading..."
                  : "Upload"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="rounded-xl border bg-card p-6">
        <div className="flex items-start gap-3">
          <Info
            size={22}
            className="mt-1 text-primary"
          />

          <div>
            <h3 className="font-semibold">
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