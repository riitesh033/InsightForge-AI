import {
  Download,
  Pencil,
  Trash2,
  Table,
} from "lucide-react";

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
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm transition hover:shadow-md">

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

      <div className="mt-5 grid grid-cols-2 gap-4">

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

      </div>

      <div className="mt-6 flex gap-2">

        <button
          onClick={() => downloadDataset(dataset.id)}
          className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground transition hover:opacity-90"
        >
          <Download size={16} />
          Download
        </button>

        <button
          className="rounded-lg border border-border p-2 hover:bg-muted"
        >
          <Pencil size={18} />
        </button>

        <button
          className="rounded-lg border border-border p-2 hover:bg-red-500/10 hover:text-red-500"
        >
          <Trash2 size={18} />
        </button>

      </div>

    </div>
  );
}