import { useState } from "react";
import {
  BarChart3,
  Download,
  FileCheck2,
  FileSpreadsheet,
  Pencil,
  Table,
  Trash2,
} from "lucide-react";
import { Link } from "react-router-dom";

import DeleteDatasetDialog from "@/components/datasets/DeleteDatasetDialog";
import RenameDatasetDialog from "@/components/datasets/RenameDatasetDialog";

import {
  Dataset,
  deleteDataset,
  downloadDataset,
  downloadCleanedDataset,
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
  const [renameOpen, setRenameOpen] =
    useState(false);

  const [deleteOpen, setDeleteOpen] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [downloadLoading, setDownloadLoading] =
    useState<"original" | "cleaned" | null>(
      null
    );

  async function handleRename(name: string) {
    if (!name.trim()) {
      return;
    }

    try {
      setLoading(true);

      const updatedDataset =
        await renameDataset(
          dataset.id,
          name.trim()
        );

      onRename(updatedDataset);

      setRenameOpen(false);
    } catch (error) {
      console.error(
        "Rename failed:",
        error
      );
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
      console.error(
        "Delete failed:",
        error
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleDownloadOriginal() {
    try {
      setDownloadLoading("original");

      await downloadDataset(
        dataset.id,
        dataset.file_type.toLowerCase() as "csv" | "xlsx"
      );
    } catch (error) {
      console.error(
        "Original dataset download failed:",
        error
      );
    } finally {
      setDownloadLoading(null);
    }
  }

  async function handleDownloadCleaned(
    format: "csv" | "xlsx"
  ) {
    if (!dataset.cleaned_available) {
      return;
    }

    try {
      setDownloadLoading("cleaned");

      await downloadCleanedDataset(
        dataset.id,
        format
      );
    } catch (error) {
      console.error(
        "Cleaned dataset download failed:",
        error
      );
    } finally {
      setDownloadLoading(null);
    }
  }

  const isBusy =
    loading ||
    downloadLoading !== null;

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

        {/* Dataset Status */}
        <div className="mt-5 flex flex-wrap gap-2">

          <span className="inline-flex items-center gap-1.5 rounded-full bg-muted px-3 py-1 text-xs font-medium">
            <FileSpreadsheet className="h-3.5 w-3.5" />
            Original
          </span>

          {dataset.cleaned_available ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
              <FileCheck2 className="h-3.5 w-3.5" />
              Cleaned Available
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-dashed px-3 py-1 text-xs font-medium text-muted-foreground">
              <FileCheck2 className="h-3.5 w-3.5" />
              Not Cleaned
            </span>
          )}

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
              {dataset.columns}
            </p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground">
              File Size
            </p>

            <p className="font-semibold">
              {formatFileSize(
                dataset.file_size
              )}
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
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2 text-primary-foreground transition hover:opacity-90"
        >
          <BarChart3 className="h-4 w-4" />

          View Analysis
        </Link>

        {/* Original Download */}
        <button
          type="button"
          onClick={
            handleDownloadOriginal
          }
          disabled={isBusy}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border px-4 py-2 transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Download className="h-4 w-4" />

          {downloadLoading === "original"
            ? "Downloading..."
            : "Download Original"}
        </button>

        {/* Cleaned Dataset */}
        <div className="mt-4 rounded-xl border border-dashed p-4">

          <div className="flex items-start gap-3">

            <div className="rounded-lg bg-primary/10 p-2">
              <FileCheck2 className="h-4 w-4 text-primary" />
            </div>

            <div className="min-w-0 flex-1">

              <p className="text-sm font-medium">
                Cleaned Dataset
              </p>

              {dataset.cleaned_available ? (
                <p className="mt-1 truncate text-xs text-muted-foreground">
                  {dataset.cleaned_filename}
                </p>
              ) : (
                <p className="mt-1 text-xs text-muted-foreground">
                  Apply cleaning from the Analysis page to create a cleaned dataset.
                </p>
              )}

            </div>

          </div>

          <div className="mt-3 grid grid-cols-2 gap-2">

            <button
              type="button"
              onClick={() =>
                handleDownloadCleaned(
                  "csv"
                )
              }
              disabled={
                isBusy ||
                !dataset.cleaned_available
              }
              className="flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Download className="h-3.5 w-3.5" />

              {downloadLoading === "cleaned"
                ? "Downloading..."
                : "CSV"}
            </button>

            <button
              type="button"
              onClick={() =>
                handleDownloadCleaned(
                  "xlsx"
                )
              }
              disabled={
                isBusy ||
                !dataset.cleaned_available
              }
              className="flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Download className="h-3.5 w-3.5" />

              {downloadLoading === "cleaned"
                ? "Downloading..."
                : "XLSX"}
            </button>

          </div>

        </div>

        {/* Actions */}
        <div className="mt-4 flex gap-2">

          <button
            type="button"
            onClick={() =>
              setRenameOpen(true)
            }
            disabled={isBusy}
            className="flex flex-1 items-center justify-center gap-2 rounded-xl border px-4 py-2 transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Pencil className="h-4 w-4" />

            Rename
          </button>

          <button
            type="button"
            onClick={() =>
              setDeleteOpen(true)
            }
            disabled={isBusy}
            className="rounded-xl border p-2 transition hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-950 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Delete dataset"
          >
            <Trash2 className="h-4 w-4" />
          </button>

        </div>

      </div>

      <RenameDatasetDialog
        open={renameOpen}
        currentName={
          dataset.original_filename
        }
        loading={loading}
        onClose={() =>
          setRenameOpen(false)
        }
        onSave={handleRename}
      />

      <DeleteDatasetDialog
        open={deleteOpen}
        datasetName={
          dataset.original_filename
        }
        loading={loading}
        onClose={() =>
          setDeleteOpen(false)
        }
        onDelete={handleDelete}
      />
    </>
  );
}
