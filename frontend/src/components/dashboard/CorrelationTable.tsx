interface Props {
  correlations: Record<
    string,
    Record<string, number>
  >;
}

export default function CorrelationTable({
  correlations,
}: Props) {
  const columns = Object.keys(correlations);

  if (!columns.length) {
    return null;
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">

      <div className="border-b border-border p-6">
        <h2 className="text-xl font-semibold">
          Correlation Matrix
        </h2>
      </div>

      <div className="overflow-x-auto">

        <table className="min-w-full">

          <thead>

            <tr>

              <th className="px-4 py-3"></th>

              {columns.map((column) => (
                <th
                  key={column}
                  className="px-4 py-3"
                >
                  {column}
                </th>
              ))}

            </tr>

          </thead>

          <tbody>

            {columns.map((row) => (

              <tr key={row}>

                <td className="px-4 py-3 font-semibold">
                  {row}
                </td>

                {columns.map((column) => (

                  <td
                    key={column}
                    className="px-4 py-3 text-center"
                  >
                    {correlations[row][column]}
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