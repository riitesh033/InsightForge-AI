interface Props {
  statistics: Record<string, Record<string, any>>;
}

export default function StatisticsTable({
  statistics,
}: Props) {
  const columns = Object.keys(statistics);

  if (!columns.length) {
    return null;
  }

  const metrics = Object.keys(
    statistics[columns[0]]
  );

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">

      <div className="border-b border-border p-6">

        <h2 className="text-xl font-semibold text-foreground">
          Statistical Summary
        </h2>

      </div>

      <div className="overflow-x-auto">

        <table className="min-w-full">

          <thead className="bg-muted/40">

            <tr>

              <th className="px-4 py-3 text-left">
                Statistic
              </th>

              {columns.map((column) => (
                <th
                  key={column}
                  className="px-4 py-3 text-center"
                >
                  {column}
                </th>
              ))}

            </tr>

          </thead>

          <tbody>

            {metrics.map((metric) => (

              <tr
                key={metric}
                className="border-t border-border hover:bg-muted/20"
              >

                <td className="px-4 py-3 font-medium">
                  {metric}
                </td>

                {columns.map((column) => (

                  <td
                    key={column}
                    className="px-4 py-3 text-center"
                  >
                    {String(
                      statistics[column][metric]
                    )}
                  </td>

                ))}

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    </div>
  );
}