interface ColumnInfo {
  name: string;
  dtype: string;
  missing: number;
  missing_percent: number;
  unique: number;
  memory_usage: number;
}

interface Props {
  columns: ColumnInfo[];
}

export default function ColumnTable({
  columns,
}: Props) {
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">

      <div className="border-b border-border p-6">
        <h2 className="text-xl font-semibold text-foreground">
          Column Information
        </h2>
      </div>

      <div className="overflow-x-auto">

        <table className="min-w-full">

          <thead className="bg-muted/50">

            <tr>

              <th className="px-4 py-3 text-left">
                Column
              </th>

              <th className="px-4 py-3 text-left">
                Data Type
              </th>

              <th className="px-4 py-3 text-center">
                Missing
              </th>

              <th className="px-4 py-3 text-center">
                Missing %
              </th>

              <th className="px-4 py-3 text-center">
                Unique
              </th>

              <th className="px-4 py-3 text-center">
                Memory
              </th>

            </tr>

          </thead>

          <tbody>

            {columns.map((column) => (

              <tr
                key={column.name}
                className="border-t border-border hover:bg-muted/30"
              >

                <td className="px-4 py-3 font-medium">
                  {column.name}
                </td>

                <td className="px-4 py-3">
                  {column.dtype}
                </td>

                <td className="px-4 py-3 text-center">
                  {column.missing}
                </td>

                <td className="px-4 py-3 text-center">
                  {column.missing_percent}%
                </td>

                <td className="px-4 py-3 text-center">
                  {column.unique}
                </td>

                <td className="px-4 py-3 text-center">
                  {(column.memory_usage / 1024).toFixed(2)} KB
                </td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    </div>
  );
}