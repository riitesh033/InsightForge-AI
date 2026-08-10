interface ColumnInfo {
  name: string;
  dtype: string;
  unique: number;
  missing: number;
  missing_percent?: number;
  memory_usage?: number;
  mean?: number | null;
  std?: number | null;
}

interface Props {
  columnInfo: ColumnInfo[];
  statistics?: Record<string, any>;
}

export default function ColumnInfoTable({
  columnInfo,
}: Props) {
  const columns = Array.isArray(columnInfo)
    ? columnInfo
    : [];

  return (
    <div className="rounded-2xl border bg-card shadow-sm">

      {/* Header */}
      <div className="border-b p-6">

        <h2 className="text-xl font-semibold">
          Column Information
        </h2>

        <p className="mt-1 text-sm text-muted-foreground">
          Detailed information about every dataset column.
        </p>

      </div>

      {/* Table */}
      <div className="overflow-x-auto">

        <table className="w-full">

          <thead className="bg-muted/40">

            <tr>

              <th className="px-5 py-3 text-left">
                Column
              </th>

              <th className="px-5 py-3 text-left">
                Data Type
              </th>

              <th className="px-5 py-3 text-center">
                Unique
              </th>

              <th className="px-5 py-3 text-center">
                Missing
              </th>

              <th className="px-5 py-3 text-center">
                Mean
              </th>

              <th className="px-5 py-3 text-center">
                Std
              </th>

            </tr>

          </thead>

          <tbody>

            {columns.length === 0 ? (

              <tr>

                <td
                  colSpan={6}
                  className="py-10 text-center text-muted-foreground"
                >
                  No column information available.
                </td>

              </tr>

            ) : (

              columns.map((info) => {

                const columnName = info.name;

                const isNumeric =
                  typeof info.mean === "number" ||
                  typeof info.std === "number";

                return (

                  <tr
                    key={columnName}
                    className="border-t transition-colors hover:bg-muted/30"
                  >

                    {/* Column Name */}
                    <td className="px-5 py-4 font-medium">
                      {columnName}
                    </td>

                    {/* Data Type */}
                    <td className="px-5 py-4">
                      {info.dtype ?? "-"}
                    </td>

                    {/* Unique */}
                    <td className="px-5 py-4 text-center">
                      {info.unique ?? "-"}
                    </td>

                    {/* Missing */}
                    <td className="px-5 py-4 text-center">
                      {info.missing ?? 0}
                    </td>

                    {/* Mean */}
                    <td className="px-5 py-4 text-center">
                      {isNumeric &&
                      typeof info.mean === "number"
                        ? info.mean.toFixed(2)
                        : "-"}
                    </td>

                    {/* Standard Deviation */}
                    <td className="px-5 py-4 text-center">
                      {isNumeric &&
                      typeof info.std === "number"
                        ? info.std.toFixed(2)
                        : "-"}
                    </td>

                  </tr>

                );
              })

            )}

          </tbody>

        </table>

      </div>

    </div>
  );
}