import { useState } from "react";
import {
  Download,
  Pencil,
  Table,
  Trash2,
  BarChart3,
} from "lucide-react";
import { Link } from "react-router-dom";

import RenameDatasetDialog from "@/components/dashboard/RenameDatasetDialog";
import DeleteDatasetDialog from "@/components/dashboard/DeleteDatasetDialog";

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
  const [renameOpen, setRenameOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleRename(name: string) {
    if (!name.trim()) return;

    try {
      setLoading(true);

      const updated = await renameDataset(
        dataset.id,
        name.trim()
      );

      onRename(updated);

      setRenameOpen(false);
    } catch (error) {
      console.error(error);
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
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
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

        {/* Buttons */}
        <div className="mt-4 flex gap-2">

          <button
            onClick={() => downloadDataset(dataset.id)}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-border px-4 py-2 transition hover:bg-muted"
          >
            <Download size={16} />
            Download
          </button>

          <button
            onClick={() => setRenameOpen(true)}
            className="rounded-lg border border-border p-2 transition hover:bg-muted"
          >
            <Pencil size={18} />
          </button>

          <button
            onClick={() => setDeleteOpen(true)}
            className="rounded-lg border border-border p-2 transition hover:bg-red-500/10 hover:text-red-500"
          >
            <Trash2 size={18} />
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