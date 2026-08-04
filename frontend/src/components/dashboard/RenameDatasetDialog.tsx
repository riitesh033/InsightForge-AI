import { useEffect, useState } from "react";

interface Props {
  open: boolean;
  currentName: string;
  loading?: boolean;
  onClose: () => void;
  onSave: (name: string) => void;
}

export default function RenameDatasetDialog({
  open,
  currentName,
  loading = false,
  onClose,
  onSave,
}: Props) {
  const [name, setName] = useState(currentName);

  useEffect(() => {
    setName(currentName);
  }, [currentName]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl">

        <h2 className="text-2xl font-bold">
          Rename Dataset
        </h2>

        <p className="mt-2 text-muted-foreground">
          Enter a new dataset name.
        </p>

        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-6 w-full rounded-lg border border-border bg-background px-4 py-3 outline-none focus:border-primary"
        />

        <div className="mt-8 flex justify-end gap-3">

          <button
            onClick={onClose}
            className="rounded-lg border border-border px-5 py-2"
          >
            Cancel
          </button>

          <button
            disabled={loading}
            onClick={() => onSave(name)}
            className="rounded-lg bg-primary px-5 py-2 text-primary-foreground disabled:opacity-50"
          >
            {loading ? "Saving..." : "Save"}
          </button>

        </div>

      </div>
    </div>
  );
}