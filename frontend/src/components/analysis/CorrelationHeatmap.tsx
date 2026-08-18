interface Props {
  correlations?: Record<string, Record<string, number>>;
}

function getCellClass(value: number) {
  const intensity = Math.min(Math.abs(value), 1);

  if (value >= 0) {
    if (intensity >= 0.8) {
      return "bg-green-600 text-white";
    }

    if (intensity >= 0.5) {
      return "bg-green-400 text-white";
    }

    if (intensity >= 0.2) {
      return "bg-green-200 text-green-900 dark:bg-green-900 dark:text-green-200";
    }

    return "bg-muted";
  }

  if (intensity >= 0.8) {
    return "bg-red-600 text-white";
  }

  if (intensity >= 0.5) {
    return "bg-red-400 text-white";
  }

  if (intensity >= 0.2) {
    return "bg-red-200 text-red-900 dark:bg-red-900 dark:text-red-200";
  }

  return "bg-muted";
}

export default function CorrelationHeatmap({
  correlations,
}: Props) {
  if (!correlations || Object.keys(correlations).length === 0) {
    return (
      <div className="rounded-2xl border bg-card p-6 shadow-sm">
        <h2 className="text-xl font-semibold">
          Correlation Analysis
        </h2>

        <p className="mt-1 text-sm text-muted-foreground">
          No correlation data is available for this dataset.
        </p>
      </div>
    );
  }

  const columns = Object.keys(correlations);

  return (
    <div className="rounded-2xl border bg-card p-6 shadow-sm">

      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold">
          Correlation Analysis
        </h2>

        <p className="mt-1 text-sm text-muted-foreground">
          Shows relationships between numerical columns.
        </p>
      </div>

      {/* Legend */}
      <div className="mt-5 flex flex-wrap items-center gap-4 text-sm">

        <div className="flex items-center gap-2">
          <span className="h-4 w-4 rounded bg-green-600" />
          <span>Strong positive</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="h-4 w-4 rounded bg-red-600" />
          <span>Strong negative</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="h-4 w-4 rounded bg-muted" />
          <span>Weak / none</span>
        </div>

      </div>

      {/* Matrix */}
      <div className="mt-6 overflow-x-auto">

        <table className="border-collapse">

          <thead>
            <tr>

              <th className="sticky left-0 z-10 min-w-[120px] bg-card px-4 py-3 text-left text-sm font-semibold">
                Column
              </th>

              {columns.map((column) => (
                <th
                  key={column}
                  className="min-w-[90px] px-3 py-3 text-center text-sm font-semibold"
                >
                  {column}
                </th>
              ))}

            </tr>
          </thead>

          <tbody>

            {columns.map((row) => (
              <tr key={row}>

                <td className="sticky left-0 z-10 border-t bg-card px-4 py-3 text-sm font-medium">
                  {row}
                </td>

                {columns.map((column) => {

                  const rawValue =
                    correlations[row]?.[column];

                  const value =
                    typeof rawValue === "number"
                      ? rawValue
                      : Number(rawValue);

                  const safeValue =
                    Number.isFinite(value)
                      ? Math.max(-1, Math.min(1, value))
                      : 0;

                  return (
                    <td
                      key={column}
                      className="border-t px-2 py-2 text-center"
                    >

                      <div
                        title={`${row} ↔ ${column}: ${safeValue.toFixed(2)}`}
                        className={`flex h-12 min-w-[70px] items-center justify-center rounded-lg text-sm font-semibold transition-transform hover:scale-105 ${getCellClass(
                          safeValue
                        )}`}
                      >
                        {safeValue.toFixed(2)}
                      </div>

                    </td>
                  );
                })}

              </tr>
            ))}

          </tbody>

        </table>

      </div>

      {/* Interpretation */}
      <div className="mt-6 rounded-xl bg-muted/40 p-4">

        <p className="text-sm font-medium">
          How to interpret
        </p>

        <p className="mt-1 text-sm text-muted-foreground">
          Values close to +1 indicate a strong positive
          relationship, while values close to -1 indicate
          a strong negative relationship. Values near 0
          indicate little linear relationship.
        </p>

      </div>

    </div>
  );
}