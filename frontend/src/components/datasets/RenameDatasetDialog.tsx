import { useEffect, useState } from "react";

interface Props {
  open: boolean;
  currentName: string;
  loading: boolean;
  onClose: () => void;
  onSave: (name: string) => void | Promise<void>;
}

export default function RenameDatasetDialog({
  open,
  currentName,
  loading,
  onClose,
  onSave,
}: Props) {
  const [name, setName] = useState(currentName);

  useEffect(() => {
    if (open) {
      setName(currentName);
    }
  }, [currentName, open]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-2xl border bg-card p-6 shadow-xl">

        <h2 className="text-xl font-semibold">
          Rename Dataset
        </h2>


        <input
          value={name}
          onChange={(e) =>
            setName(e.target.value)
          }
          className="mt-5 w-full rounded-xl border bg-background px-4 py-3"
          placeholder="Dataset name"
        />


        <div className="mt-6 flex justify-end gap-3">

          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="rounded-lg border px-4 py-2 hover:bg-muted disabled:opacity-50"
          >
            Cancel
          </button>


          <button
            type="button"
            onClick={() =>
              onSave(name.trim())
            }
            disabled={
              loading || !name.trim()
            }
            className="rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50"
          >
            {loading ? "Saving..." : "Save"}
          </button>

        </div>

      </div>
    </div>
  );
}