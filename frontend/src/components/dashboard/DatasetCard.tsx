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
  deleteDataset,
  downloadDataset,
  renameDataset,
} from "@/services/dataset";

interface Props {
  dataset: Dataset;
  onDelete: (id: number) => void;
  onRename: (dataset: Dataset) => void;
}

export default function DatasetCard({
  dataset,
  onDelete,
  onRename,
}: Props) {
  async function handleDelete() {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${dataset.original_filename}"?`
    );

    if (!confirmed) return;

    try {
      await deleteDataset(dataset.id);

      onDelete(dataset.id);

      alert("Dataset deleted successfully.");
    } catch (error: any) {
      console.error(error);

      alert(
        error?.response?.data?.detail ??
          "Failed to delete dataset."
      );
    }
  }

  async function handleRename() {
    const input = window.prompt(
      "Enter a new dataset name:",
      dataset.original_filename
    );

    if (input === null) return;

    const newName = input.trim();

    if (!newName) {
      alert("Dataset name cannot be empty.");
      return;
    }

    if (newName === dataset.original_filename) {
      return;
    }

    try {
      const updated = await renameDataset(
        dataset.id,
        newName
      );

      onRename(updated);

      alert("Dataset renamed successfully.");
    } catch (error: any) {
      console.error(error);

      alert(
        error?.response?.data?.detail ??
          "Failed to rename dataset."
      );
    }
  }

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

      {/* Information */}
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
            {new Date(
              dataset.uploaded_at
            ).toLocaleDateString()}
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
          type="button"
          onClick={() => downloadDataset(dataset.id)}
          className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-border px-4 py-2 transition hover:bg-muted"
        >
          <Download size={16} />
          Download
        </button>

        <button
          type="button"
          onClick={handleRename}
          className="rounded-lg border border-border p-2 transition hover:bg-muted"
          title="Rename Dataset"
        >
          <Pencil size={18} />
        </button>

        <button
          type="button"
          onClick={handleDelete}
          className="rounded-lg border border-border p-2 transition hover:bg-red-500/10 hover:text-red-500"
          title="Delete Dataset"
        >
          <Trash2 size={18} />
        </button>
      </div>
    </div>
  );
}