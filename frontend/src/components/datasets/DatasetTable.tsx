import { useState } from "react";
import {
  Download,
  Eye,
  Pencil,
  Trash2,
} from "lucide-react";

import DeleteDatasetDialog from "@/components/datasets/DeleteDatasetDialog";
import RenameDatasetDialog from "@/components/datasets/RenameDatasetDialog";

import {
  Dataset,
  deleteDataset,
  downloadDataset,
  renameDataset,
} from "@/services/dataset";

interface Props {
  datasets: Dataset[];
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DatasetTable({
  datasets,
}: Props) {
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [renameOpen, setRenameOpen] = useState(false);

  const [selectedDataset, setSelectedDataset] =
    useState<Dataset | null>(null);

  return (
    <>
      <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
        <div className="border-b p-5">
          <h2 className="text-lg font-semibold">
            Uploaded Datasets
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/40">
              <tr>
                <th className="px-4 py-3 text-left">
                  Dataset
                </th>

                <th className="px-4 py-3 text-center">
                  Rows
                </th>

                <th className="px-4 py-3 text-center">
                  Columns
                </th>

                <th className="px-4 py-3 text-center">
                  Size
                </th>

                <th className="px-4 py-3 text-center">
                  Uploaded
                </th>

                <th className="px-4 py-3 text-center">
                  Actions
                </th>
              </tr>
            </thead>

            <tbody>
              {datasets.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="py-10 text-center text-muted-foreground"
                  >
                    No datasets found.
                  </td>
                </tr>
              ) : (
                datasets.map((dataset) => (
                  <tr
                    key={dataset.id}
                    className="border-t hover:bg-muted/30"
                  >
                    <td className="px-4 py-4 font-medium">
                      {dataset.original_filename}
                    </td>

                    <td className="px-4 py-4 text-center">
                      {dataset.rows.toLocaleString()}
                    </td>

                    <td className="px-4 py-4 text-center">
                      {dataset.columns}
                    </td>

                    <td className="px-4 py-4 text-center">
                      {formatFileSize(
                        dataset.file_size
                      )}
                    </td>

                    <td className="px-4 py-4 text-center">
                      {new Date(
                        dataset.uploaded_at
                      ).toLocaleDateString()}
                    </td>

                    <td className="px-4 py-4">
                      <div className="flex justify-center gap-2">
                        <button
                          onClick={() => {
                            setSelectedDataset(dataset);
                            setRenameOpen(true);
                          }}
                          className="rounded-lg p-2 hover:bg-muted"
                          title="Rename"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>

                        <button
                          className="rounded-lg p-2 hover:bg-muted"
                          title="View Analysis"
                        >
                          <Eye className="h-4 w-4" />
                        </button>

                        <button
                          onClick={() =>
                            downloadDataset(dataset.id)
                          }
                          className="rounded-lg p-2 hover:bg-muted"
                          title="Download"
                        >
                          <Download className="h-4 w-4" />
                        </button>

                        <button
                          onClick={() => {
                            setSelectedDataset(dataset);
                            setDeleteOpen(true);
                          }}
                          className="rounded-lg p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-950"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <DeleteDatasetDialog
        open={deleteOpen}
        datasetName={
          selectedDataset?.original_filename ?? ""
        }
        loading={false}
        onClose={() => setDeleteOpen(false)}
        onDelete={async () => {
          if (!selectedDataset) return;

          try {
            await deleteDataset(selectedDataset.id);

            setDeleteOpen(false);
            window.location.reload();
          } catch (error) {
            console.error(error);
            alert("Failed to delete dataset.");
          }
        }}
      />

      <RenameDatasetDialog
        open={renameOpen}
        currentName={
          selectedDataset?.original_filename ?? ""
        }
        loading={false}
        onClose={() => setRenameOpen(false)}
        onSave={async (name) => {
          if (!selectedDataset) return;

          try {
            await renameDataset(
              selectedDataset.id,
              name
            );

            setRenameOpen(false);
            window.location.reload();
          } catch (error) {
            console.error(error);
            alert("Failed to rename dataset.");
          }
        }}
      />
    </>
  );
}