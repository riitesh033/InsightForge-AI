import { useState } from "react";
import {
  BarChart3,
  Download,
  Pencil,
  Table,
  Trash2,
} from "lucide-react";
import { Link } from "react-router-dom";

import DeleteDatasetDialog from "@/components/dashboard/DeleteDatasetDialog";
import RenameDatasetDialog from "@/components/dashboard/RenameDatasetDialog";

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

function formatFileSize(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(2)} KB`;
  }

  if (bytes < 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export default function DatasetCard({
  dataset,
  onDelete,
  onRename,
}: Props) {
  const [renameOpen, setRenameOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleRename(name: string) {
    if (!name.trim()) {
      return;
    }

    try {
      setLoading(true);

      const updatedDataset = await renameDataset(
        dataset.id,
        name.trim()
      );

      onRename(updatedDataset);

      setRenameOpen(false);
    } catch (error) {
      console.error("Rename failed:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    try {
      setLoading(true);

      await deleteDataset(dataset.id);

      onDelete(dataset.id);

      setDeleteOpen(false);
    } catch (error) {
      console.error("Delete failed:", error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="rounded-2xl border bg-card p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-lg font-semibold">
              {dataset.original_filename}
            </h3>

            <p className="mt-1 text-sm text-muted-foreground">
              {dataset.file_type.toUpperCase()}
            </p>
          </div>

          <div className="rounded-xl bg-primary/10 p-3">
            <Table className="h-5 w-5 text-primary" />
          </div>
        </div>

        {/* Stats */}
        <div className="mt-6 grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">
              Rows
            </p>

            <p className="font-semibold">
              {dataset.rows.toLocaleString()}
            </p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground">
              Columns
            </p>

            <p className="font-semibold">
              {dataset.columns.toLocaleString()}
            </p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground">
              File Size
            </p>

            <p className="font-semibold">
              {formatFileSize(dataset.file_size)}
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
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2 text-primary-foreground transition hover:opacity-90"
        >
          <BarChart3 className="h-4 w-4" />
          View Analysis
        </Link>

        {/* Actions */}
        <div className="mt-4 flex gap-2">
          <button
            type="button"
            onClick={() => downloadDataset(dataset.id)}
            disabled={loading}
            className="flex flex-1 items-center justify-center gap-2 rounded-xl border px-4 py-2 transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            Download
          </button>

          <button
            type="button"
            onClick={() => setRenameOpen(true)}
            disabled={loading}
            className="rounded-xl border p-2 transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Pencil className="h-4 w-4" />
          </button>

          <button
            type="button"
            onClick={() => setDeleteOpen(true)}
            disabled={loading}
            className="rounded-xl border p-2 transition hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-950 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      <RenameDatasetDialog
        open={renameOpen}
        currentName={dataset.original_filename}
        loading={loading}
        onClose={() => setRenameOpen(false)}
        onSave={handleRename}
      />

      <DeleteDatasetDialog
        open={deleteOpen}
        datasetName={dataset.original_filename}
        loading={loading}
        onClose={() => setDeleteOpen(false)}
        onDelete={handleDelete}
      />
    </>
  );
}