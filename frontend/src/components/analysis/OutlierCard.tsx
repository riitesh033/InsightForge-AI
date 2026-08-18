import {
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

interface Props {
  outliers?: Record<string, any>;
}

export default function OutlierCard({
  outliers,
}: Props) {
  if (!outliers) {
    return null;
  }

  const columns = Object.entries(outliers)
    .map(([column, value]) => {
      let count = 0;

      if (typeof value === "number") {
        count = value;
      } else if (
        typeof value === "object" &&
        value !== null
      ) {
        count =
          Number(
            value.count ??
            value.outliers ??
            value.outlier_count ??
            0
          ) || 0;
      }

      return {
        column,
        count,
      };
    })
    .filter((item) => item.count > 0)
    .sort((a, b) => b.count - a.count);

  const totalOutliers = columns.reduce(
    (total, item) => total + item.count,
    0
  );

  return (
    <div className="rounded-2xl border bg-card p-6 shadow-sm">

      {/* Header */}
      <div className="flex items-start gap-4">

        <div
          className={`rounded-xl p-3 ${
            totalOutliers > 0
              ? "bg-red-500/10"
              : "bg-green-500/10"
          }`}
        >
          {totalOutliers > 0 ? (
            <AlertTriangle className="h-6 w-6 text-red-500" />
          ) : (
            <CheckCircle2 className="h-6 w-6 text-green-500" />
          )}
        </div>

        <div>
          <h2 className="text-xl font-semibold">
            Outlier Detection
          </h2>

          <p className="text-sm text-muted-foreground">
            Abnormal values detected in numerical columns.
          </p>
        </div>

      </div>

      {/* Summary */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2">

        <div className="rounded-xl bg-muted/40 p-4">
          <p className="text-sm text-muted-foreground">
            Total Outliers
          </p>

          <p className="mt-1 text-2xl font-bold">
            {totalOutliers}
          </p>
        </div>

        <div className="rounded-xl bg-muted/40 p-4">
          <p className="text-sm text-muted-foreground">
            Columns Affected
          </p>

          <p className="mt-1 text-2xl font-bold">
            {columns.length}
          </p>
        </div>

      </div>

      {/* Results */}
      <div className="mt-6 space-y-3">

        {columns.length === 0 ? (
          <div className="flex items-center gap-3 rounded-xl border border-green-500/20 bg-green-500/5 p-4">

            <CheckCircle2 className="h-5 w-5 text-green-500" />

            <div>
              <p className="font-medium">
                No outliers detected
              </p>

              <p className="text-sm text-muted-foreground">
                No unusual values were found in the
                analyzed numerical columns.
              </p>
            </div>

          </div>
        ) : (
          columns.map(({ column, count }) => (

            <div
              key={column}
              className="rounded-xl border p-4"
            >

              <div className="flex items-center justify-between">

                <span className="font-medium">
                  {column}
                </span>

                <span className="font-semibold">
                  {count}
                </span>

              </div>

              <div className="mt-3 h-2 overflow-hidden rounded-full bg-muted">

                <div
                  className="h-full rounded-full bg-red-500 transition-all"
                  style={{
                    width: `${Math.min(
                      (count / totalOutliers) * 100,
                      100
                    )}%`,
                  }}
                />

              </div>

              <p className="mt-2 text-xs text-muted-foreground">
                {totalOutliers > 0
                  ? `${(
                      (count / totalOutliers) *
                      100
                    ).toFixed(1)}% of detected outliers`
                  : "No outliers"}
              </p>

            </div>

          ))
        )}

      </div>

    </div>
  );
}