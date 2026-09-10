interface ColumnInfo {
  name: string;
  dtype: string;
  unique: number;
  missing: number;
  missing_percentage?: number | null;
  memory_usage?: number | null;
}

interface ColumnStatistics {
  mean?: number | null;
  standard_deviation?: number | null;
  std?: number | null;
  [key: string]: any;
}

interface Props {
  columnInfo: ColumnInfo[];
  statistics?: Record<string, ColumnStatistics>;
}

export default function ColumnInfoTable({
  columnInfo,
  statistics = {},
}: Props) {
  const columns = Array.isArray(columnInfo)
    ? columnInfo
    : [];

  const formatNumber = (value: unknown): string => {
    if (
      typeof value === "number" &&
      Number.isFinite(value)
    ) {
      return value.toLocaleString(undefined, {
        maximumFractionDigits: 2,
      });
    }

    return "-";
  };

  const formatPercent = (value: unknown): string => {
    if (
      typeof value === "number" &&
      Number.isFinite(value)
    ) {
      return `${value.toFixed(2)}%`;
    }

    return "-";
  };

  const getMissingClass = (percent: number) => {
    if (percent === 0) {
      return "text-green-600 dark:text-green-400";
    }

    if (percent < 10) {
      return "text-yellow-600 dark:text-yellow-400";
    }

    return "text-red-600 dark:text-red-400";
  };

  return (
    <div className="rounded-2xl border bg-card shadow-sm">

      {/* =====================================================
          Header
      ====================================================== */}

      <div className="border-b p-6">

        <h2 className="text-xl font-semibold">
          Column Information
        </h2>

        <p className="mt-1 text-sm text-muted-foreground">
          Detailed information about every dataset column.
        </p>

      </div>

      {/* =====================================================
          Table
      ====================================================== */}

      <div className="overflow-x-auto">

        <table className="w-full min-w-[800px]">

          <thead className="bg-muted/40">

            <tr>

              <th className="px-5 py-3 text-left text-sm font-semibold">
                Column
              </th>

              <th className="px-5 py-3 text-left text-sm font-semibold">
                Data Type
              </th>

              <th className="px-5 py-3 text-center text-sm font-semibold">
                Unique
              </th>

              <th className="px-5 py-3 text-center text-sm font-semibold">
                Missing
              </th>

              <th className="px-5 py-3 text-center text-sm font-semibold">
                Missing %
              </th>

              <th className="px-5 py-3 text-center text-sm font-semibold">
                Mean
              </th>

              <th className="px-5 py-3 text-center text-sm font-semibold">
                Std
              </th>

            </tr>

          </thead>

          <tbody>

            {columns.length === 0 ? (

              <tr>

                <td
                  colSpan={7}
                  className="py-10 text-center text-muted-foreground"
                >
                  No column information available.
                </td>

              </tr>

            ) : (

              columns.map((info) => {

                const columnName = info.name;

                const stats =
                  statistics[columnName] ?? {};

                const mean = stats.mean;

                /*
                 * Support both:
                 * - std
                 * - standard_deviation
                 *
                 * This keeps the component compatible with
                 * the verified analysis contract.
                 */
                const std =
                  stats.standard_deviation ??
                  stats.std;

                const missing =
                  typeof info.missing === "number"
                    ? info.missing
                    : 0;

                const missingPercent =
                  typeof info.missing_percentage === "number"
                    ? info.missing_percentage
                    : 0;

                return (
                  <tr
                    key={columnName}
                    className="
                      border-t
                      transition-colors
                      hover:bg-muted/30
                    "
                  >

                    {/* Column */}

                    <td className="px-5 py-4 font-medium">
                      {columnName}
                    </td>

                    {/* Data Type */}

                    <td className="px-5 py-4">

                      <span
                        className="
                          rounded-md
                          bg-muted
                          px-2
                          py-1
                          font-mono
                          text-xs
                        "
                      >
                        {info.dtype || "-"}
                      </span>

                    </td>

                    {/* Unique */}

                    <td className="px-5 py-4 text-center">
                      {formatNumber(info.unique)}
                    </td>

                    {/* Missing */}

                    <td className="px-5 py-4 text-center">
                      {missing.toLocaleString()}
                    </td>

                    {/* Missing Percentage */}

                    <td
                      className={`
                        px-5
                        py-4
                        text-center
                        font-medium
                        ${getMissingClass(missingPercent)}
                      `}
                    >
                      {formatPercent(missingPercent)}
                    </td>

                    {/* Mean */}

                    <td className="px-5 py-4 text-center">
                      {formatNumber(mean)}
                    </td>

                    {/* Standard Deviation */}

                    <td className="px-5 py-4 text-center">
                      {formatNumber(std)}
                    </td>

                  </tr>
                );
              })

            )}

          </tbody>

        </table>

      </div>

      {/* =====================================================
          Footer
      ====================================================== */}

      {columns.length > 0 && (

        <div className="border-t px-6 py-4">

          <p className="text-xs text-muted-foreground">
            Showing {columns.length}{" "}
            {columns.length === 1
              ? "column"
              : "columns"}{" "}
            from the analyzed dataset.
          </p>

        </div>

      )}

    </div>
  );
}
