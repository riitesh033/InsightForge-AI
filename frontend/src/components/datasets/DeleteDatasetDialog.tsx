interface Props {
  open: boolean;
  datasetId: number;
  datasetName: string;
  onClose: () => void;
  onDeleted: () => void;
}

export default function DeleteDatasetDialog({
  open,
  datasetId,
  datasetName,
  onClose,
  onDeleted,
}: Props) {

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-2xl border bg-card p-6 shadow-xl">
        <h2 className="text-xl font-semibold">
          Delete Dataset
        </h2>

        <p className="mt-4 text-muted-foreground">
          Are you sure you want to delete{" "}
          <span className="font-semibold">
            {datasetName}
          </span>
          ?
        </p>

        <p className="mt-2 text-sm text-red-500">
          This action cannot be undone.
        </p>

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="rounded-lg border px-4 py-2 transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
          >
            Cancel
          </button>

          <button
            type="button"
            onClick={onDelete}
            disabled={loading}
            className="rounded-lg bg-red-600 px-4 py-2 text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Deleting..." : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}