import { useNavigate } from "react-router-dom";

import { RecentDataset } from "@/services/dashboard";

interface Props {
  datasets: RecentDataset[];
}

function formatDate(date: string) {
  return new Date(date).toLocaleDateString();
}

export default function RecentDatasetsTable({
  datasets,
}: Props) {
  const navigate = useNavigate();

  function handleDatasetClick(datasetId: number) {
    navigate(`/dashboard/analysis/${datasetId}`);
  }

  return (
    <div className="rounded-2xl border bg-card shadow-sm">
      <div className="border-b p-5">
        <h2 className="text-lg font-semibold">
          Recent Datasets
        </h2>

        <p className="mt-1 text-sm text-muted-foreground">
          Recently uploaded datasets
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="border-b bg-muted/40">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium">
                Dataset
              </th>

              <th className="px-4 py-3 text-center text-sm font-medium">
                Rows
              </th>

              <th className="px-4 py-3 text-center text-sm font-medium">
                Columns
              </th>

              <th className="px-4 py-3 text-center text-sm font-medium">
                Quality
              </th>

              <th className="px-4 py-3 text-center text-sm font-medium">
                Uploaded
              </th>
            </tr>
          </thead>

          <tbody>
            {datasets.length === 0 ? (
              <tr>
                <td
                  colSpan={5}
                  className="py-8 text-center text-muted-foreground"
                >
                  No datasets uploaded yet.
                </td>
              </tr>
            ) : (
              datasets.map((dataset) => (
                <tr
                  key={dataset.id}
                  onClick={() =>
                    handleDatasetClick(dataset.id)
                  }
                  className="cursor-pointer border-b transition-colors last:border-none hover:bg-muted/40"
                >
                  <td className="px-4 py-4">
                    <div className="font-medium">
                      {dataset.original_filename}
                    </div>

                    <div className="mt-1 text-xs text-muted-foreground">
                      Dataset #{dataset.id}
                    </div>
                  </td>

                  <td className="px-4 py-4 text-center">
                    {dataset.rows.toLocaleString()}
                  </td>

                  <td className="px-4 py-4 text-center">
                    {dataset.columns}
                  </td>

                  <td className="px-4 py-4 text-center">
                    {dataset.quality_score !== null
                      ? `${dataset.quality_score}%`
                      : "-"}
                  </td>

                  <td className="px-4 py-4 text-center text-sm text-muted-foreground">
                    {formatDate(dataset.uploaded_at)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}