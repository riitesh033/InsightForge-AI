import {
  Database,
  Search,
  Filter,
  Eye,
  Trash2,
} from "lucide-react";

export default function DatasetsPage() {
  return (
    <div className="space-y-8">

      {/* Header */}

      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">

        <div>

          <h1 className="text-3xl font-bold text-foreground">
            My Datasets
          </h1>

          <p className="mt-2 text-muted-foreground">
            Manage all uploaded datasets.
          </p>

        </div>

      </div>

      {/* Search */}

      <div className="rounded-xl border border-border bg-card p-6">

        <div className="flex flex-col gap-4 md:flex-row">

          <div className="relative flex-1">

            <Search
              className="absolute left-3 top-3 text-muted-foreground"
              size={18}
            />

            <input
              placeholder="Search datasets..."
              className="
                w-full
                rounded-lg
                border
                border-border
                bg-background
                py-2.5
                pl-10
                pr-4
                text-foreground
                focus:border-primary
                focus:outline-none
              "
            />

          </div>

          <button
            className="
              flex
              items-center
              justify-center
              gap-2
              rounded-lg
              border
              border-border
              bg-background
              px-5
              py-2
              hover:bg-accent
            "
          >
            <Filter size={18} />
            Filter
          </button>

        </div>

      </div>

      {/* Table */}

      <div className="overflow-hidden rounded-xl border border-border bg-card">

        <table className="w-full">

          <thead className="bg-muted">

            <tr>

              <th className="px-6 py-4 text-left text-sm font-semibold">
                Dataset
              </th>

              <th className="px-6 py-4 text-left text-sm font-semibold">
                Type
              </th>

              <th className="px-6 py-4 text-left text-sm font-semibold">
                Uploaded
              </th>

              <th className="px-6 py-4 text-left text-sm font-semibold">
                Status
              </th>

              <th className="px-6 py-4 text-right text-sm font-semibold">
                Actions
              </th>

            </tr>

          </thead>

          <tbody>

            <tr>

              <td
                colSpan={5}
                className="py-20 text-center"
              >

                <Database
                  size={48}
                  className="mx-auto text-muted-foreground"
                />

                <h2 className="mt-4 text-xl font-semibold text-foreground">
                  No datasets uploaded
                </h2>

                <p className="mt-2 text-muted-foreground">
                  Upload your first CSV or Excel file.
                </p>

              </td>

            </tr>

          </tbody>

        </table>

      </div>

      {/* Action Buttons Preview */}

      <div className="flex gap-3">

        <button className="rounded-lg border border-border p-3 hover:bg-accent">
          <Eye size={18} />
        </button>

        <button className="rounded-lg border border-border p-3 hover:bg-red-500 hover:text-white">
          <Trash2 size={18} />
        </button>

      </div>

    </div>
  );
}