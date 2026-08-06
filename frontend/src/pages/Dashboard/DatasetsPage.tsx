import { useEffect, useMemo, useState } from "react";
import { Search, Upload } from "lucide-react";
import { Link } from "react-router-dom";

import DatasetCard from "@/components/datasets/DatasetCard";
import {
  Dataset,
  getDatasets,
} from "@/services/dataset";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadDatasets();
  }, []);


  async function loadDatasets() {
    try {
      setLoading(true);
      setError("");

      const response = await getDatasets();

      setDatasets(response);

    } catch (err) {
      console.error(
        "Dataset loading error:",
        err
      );

      setError(
        "Failed to load datasets."
      );

    } finally {
      setLoading(false);
    }
  }


  function removeDataset(id: number) {
    setDatasets((previous) =>
      previous.filter(
        (dataset) =>
          dataset.id !== id
      )
    );
  }


  function updateDataset(updated: Dataset) {
    setDatasets((previous) =>
      previous.map(
        (dataset) =>
          dataset.id === updated.id
            ? updated
            : dataset
      )
    );
  }


  const filteredDatasets = useMemo(() => {
    return datasets.filter((dataset) =>
      dataset.original_filename
        .toLowerCase()
        .includes(
          search.toLowerCase()
        )
    );
  }, [datasets, search]);



  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <h2 className="text-lg font-medium">
          Loading datasets...
        </h2>
      </div>
    );
  }



  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center dark:border-red-900 dark:bg-red-950">

        <p className="text-red-600 dark:text-red-400">
          {error}
        </p>

        <button
          onClick={loadDatasets}
          className="mt-4 rounded-lg bg-primary px-4 py-2 text-primary-foreground hover:opacity-90"
        >
          Retry
        </button>

      </div>
    );
  }



  return (
    <div className="space-y-8">

      {/* Header */}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">

        <div>

          <h1 className="text-3xl font-bold">
            My Datasets
          </h1>

          <p className="text-muted-foreground">
            Manage all your uploaded datasets.
          </p>

        </div>


        <Link
          to="/dashboard/upload"
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground transition hover:opacity-90"
        >

          <Upload className="h-4 w-4" />

          Upload Dataset

        </Link>

      </div>



      {/* Search */}

      <div className="relative max-w-md">

        <Search
          className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
        />


        <input
          type="text"
          placeholder="Search datasets..."
          value={search}
          onChange={(e) =>
            setSearch(e.target.value)
          }
          className="w-full rounded-lg border bg-background py-2 pl-10 pr-4 outline-none transition focus:ring-2 focus:ring-primary"
        />

      </div>



      {/* Empty State */}

      {filteredDatasets.length === 0 ? (

        <div className="rounded-xl border border-dashed p-16 text-center">

          <h2 className="text-xl font-semibold">
            No datasets found
          </h2>


          <p className="mt-2 text-muted-foreground">

            {search
              ? "Try a different search term."
              : "Upload your first dataset to get started."
            }

          </p>



          {!search && (

            <Link
              to="/dashboard/upload"
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground transition hover:opacity-90"
            >

              <Upload className="h-4 w-4" />

              Upload Dataset

            </Link>

          )}

        </div>


      ) : (

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">

          {filteredDatasets.map(
            (dataset) => (

              <DatasetCard
                key={dataset.id}
                dataset={dataset}
                onDelete={removeDataset}
                onRename={updateDataset}
              />

            )
          )}

        </div>

      )}

    </div>
  );
}