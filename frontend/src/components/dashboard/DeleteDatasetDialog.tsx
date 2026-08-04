import { Trash2 } from "lucide-react";

interface Props {
  open: boolean;
  datasetName: string;
  loading?: boolean;
  onClose: () => void;
  onDelete: () => void;
}

export default function DeleteDatasetDialog({
  open,
  datasetName,
  loading = false,
  onClose,
  onDelete,
}: Props) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl">

        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10">
          <Trash2
            size={30}
            className="text-red-500"
          />
        </div>

        <h2 className="mt-5 text-center text-2xl font-bold">
          Delete Dataset
        </h2>

        <p className="mt-3 text-center text-muted-foreground">
          Are you sure you want to delete
        </p>

        <p className="mt-1 text-center font-semibold text-foreground">
          {datasetName}
        </p>

        <p className="mt-4 text-center text-sm text-red-500">
          This action cannot be undone.
        </p>

        <div className="mt-8 flex justify-end gap-3">

          <button
            onClick={onClose}
            className="rounded-lg border border-border px-5 py-2"
          >
            Cancel
          </button>

          <button
            disabled={loading}
            onClick={onDelete}
            className="rounded-lg bg-red-600 px-5 py-2 text-white transition hover:bg-red-700 disabled:opacity-50"
          >
            {loading ? "Deleting..." : "Delete"}
          </button>

        </div>

      </div>
    </div>
  );
}