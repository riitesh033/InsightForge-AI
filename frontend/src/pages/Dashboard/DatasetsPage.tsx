import { useEffect, useState } from "react";

import DatasetCard from "@/components/dashboard/DatasetCard";

import {
  Dataset,
  getDatasets,
} from "@/services/dataset";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDatasets();
  }, []);

  async function loadDatasets() {
    try {
      const data = await getDatasets();
      setDatasets(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  function removeDataset(id: number) {
    setDatasets((previous) =>
      previous.filter((dataset) => dataset.id !== id)
    );
  }

  function updateDataset(updated: Dataset) {
    setDatasets((previous) =>
      previous.map((dataset) =>
        dataset.id === updated.id ? updated : dataset
      )
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <h2 className="text-lg">Loading...</h2>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">
          My Datasets
        </h1>

        <p className="text-muted-foreground">
          Manage your uploaded datasets.
        </p>
      </div>

      {datasets.length === 0 ? (
        <div className="rounded-xl border border-dashed p-16 text-center">
          <h2 className="text-xl font-semibold">
            No datasets uploaded
          </h2>

          <p className="mt-2 text-muted-foreground">
            Upload your first dataset.
          </p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {datasets.map((dataset) => (
            <DatasetCard
              key={dataset.id}
              dataset={dataset}
              onDelete={removeDataset}
              onRename={updateDataset}
            />
          ))}
        </div>
      )}
    </div>
  );
}