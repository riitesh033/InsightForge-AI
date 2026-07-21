import { useEffect, useState } from "react";

import { Database } from "lucide-react";

import getDatasets from "@/services/dataset";

import type { Dataset } from "@/services/dataset";

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

  if (loading) {
    return (
      <div className="p-8">
        Loading datasets...
      </div>
    );
  }

  return (
    <div className="space-y-8">

      <div>

        <h1 className="text-3xl font-bold">
          My Datasets
        </h1>

        <p className="text-muted-foreground mt-2">
          Manage all uploaded datasets.
        </p>

      </div>

      {datasets.length === 0 ? (

        <div className="rounded-xl border bg-card p-12 text-center">

          <Database
            size={64}
            className="mx-auto text-muted-foreground"
          />

          <h2 className="mt-5 text-xl font-semibold">
            No datasets found
          </h2>

          <p className="mt-2 text-muted-foreground">
            Upload your first dataset.
          </p>

        </div>

      ) : (

        <div>
          Dataset list coming next...
        </div>

      )}

    </div>
  );
}