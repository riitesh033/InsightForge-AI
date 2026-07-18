import { UploadCloud, FileSpreadsheet, Info } from "lucide-react";
import { useState } from "react";

export default function UploadDatasetPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  function handleFileChange(
    e: React.ChangeEvent<HTMLInputElement>
  ) {
    if (!e.target.files?.length) return;

    setSelectedFile(e.target.files[0]);
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

      {/* Upload Card */}

      <div className="rounded-xl border border-border bg-card p-8 shadow-sm">

        <label
          htmlFor="dataset"
          className="
            flex
            cursor-pointer
            flex-col
            items-center
            justify-center
            rounded-xl
            border-2
            border-dashed
            border-border
            p-16
            transition
            hover:border-primary
            hover:bg-accent/30
          "
        >

          <UploadCloud
            className="text-primary"
            size={60}
          />

          <h2 className="mt-6 text-2xl font-semibold text-foreground">
            Drag & Drop Dataset
          </h2>

          <p className="mt-3 text-center text-muted-foreground">
            or click here to browse files
          </p>

          <p className="mt-2 text-sm text-muted-foreground">
            Supported formats: CSV, XLSX, XLS
          </p>

          <input
            id="dataset"
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={handleFileChange}
          />

        </label>

      </div>

      {/* Selected File */}

      {selectedFile && (
        <div className="rounded-xl border border-border bg-card p-6">

          <div className="flex items-center gap-4">

            <div className="rounded-lg bg-primary/10 p-3">

              <FileSpreadsheet
                className="text-primary"
                size={26}
              />

            </div>

            <div className="flex-1">

              <h3 className="font-semibold text-foreground">
                {selectedFile.name}
              </h3>

              <p className="text-sm text-muted-foreground">
                {(selectedFile.size / 1024).toFixed(2)} KB
              </p>

            </div>

            <button
              className="
                rounded-lg
                bg-primary
                px-5
                py-2
                font-medium
                text-primary-foreground
                transition
                hover:opacity-90
              "
            >
              Upload
            </button>

          </div>

        </div>
      )}

      {/* Information */}

      <div className="rounded-xl border border-border bg-card p-6">

        <div className="flex items-start gap-3">

          <Info
            className="mt-1 text-primary"
            size={22}
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