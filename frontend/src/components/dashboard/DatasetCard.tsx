import {
  Download,
  Pencil,
  Table,
  Trash2,
  BarChart3,
} from "lucide-react";

import { Link } from "react-router-dom";

import {
  Dataset,
  downloadDataset,
} from "@/services/dataset";

interface Props {
  dataset: Dataset;
}

export default function DatasetCard({
  dataset,
}: Props) {
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm transition hover:shadow-lg">

      {/* Header */}
      <div className="flex items-start justify-between">

        <div>
          <h3 className="text-lg font-semibold text-foreground">
            {dataset.original_filename}
          </h3>

          <p className="mt-1 text-sm text-muted-foreground">
            {dataset.file_type.toUpperCase()}
          </p>
        </div>

        <Table
          size={22}
          className="text-primary"
        />

      </div>

      {/* Dataset Information */}
      <div className="mt-6 grid grid-cols-2 gap-4">

        <div>
          <p className="text-xs text-muted-foreground">
            Rows
          </p>

          <p className="font-semibold">
            {dataset.rows}
          </p>
        </div>

        <div>
          <p className="text-xs text-muted-foreground">
            Columns
          </p>

          <p className="font-semibold">
            {dataset.columns}
          </p>
        </div>

        <div>
          <p className="text-xs text-muted-foreground">
            File Size
          </p>

          <p className="font-semibold">
            {(dataset.file_size / 1024).toFixed(2)} KB
          </p>
        </div>

        <div>
          <p className="text-xs text-muted-foreground">
            Uploaded
          </p>

          <p className="font-semibold">
            {new Date(dataset.uploaded_at).toLocaleDateString()}
          </p>
        </div>

      </div>

      {/* View Analysis */}
      <Link
        to={`/dashboard/analysis/${dataset.id}`}
        className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground transition hover:opacity-90"
      >
        <BarChart3 size={18} />
        View Analysis
      </Link>

      {/* Action Buttons */}
      <div className="mt-4 flex gap-2">

        <button
          onClick={() => downloadDataset(dataset.id)}
          className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-border px-4 py-2 transition hover:bg-muted"
        >
          <Download size={16} />
          Download
        </button>

        <button
          className="rounded-lg border border-border p-2 transition hover:bg-muted"
        >
          <Pencil size={18} />
        </button>

        <button
          className="rounded-lg border border-border p-2 transition hover:bg-red-500/10 hover:text-red-500"
        >
          <Trash2 size={18} />
        </button>

      </div>

    </div>
  );
}