interface Props {
  score: number;
  factors?: Record<string, number>;
}

export default function QualityScore({
  score,
  factors = {},
}: Props) {
  const safeScore = Math.max(
    0,
    Math.min(100, Number(score) || 0)
  );

  const getStatus = () => {
    if (safeScore >= 75) {
      return {
        label: safeScore >= 90 ? "Excellent" : "Good",
        description: safeScore >= 90
          ? "No major data-quality issues were detected."
          : "The dataset is in good shape, with some issues worth reviewing.",
        text: "text-green-600 dark:text-green-400",
        ring: "text-green-500",
      };
    }

    if (safeScore >= 60) {
      return {
        label: "Fair",
        description: "Review the detected data-quality issues before relying on the dataset.",
        text: "text-yellow-600 dark:text-yellow-400",
        ring: "text-yellow-500",
      };
    }

    if (safeScore >= 40) {
      return {
        label: "Poor",
        description: "Several significant data-quality issues need attention.",
        text: "text-orange-600 dark:text-orange-400",
        ring: "text-orange-500",
      };
    }

    return {
      label: "Critical",
      description: "The dataset has critical quality concerns and needs substantial review.",
      text: "text-red-600 dark:text-red-400",
      ring: "text-red-500",
    };
  };

  const status = getStatus();
  const factorLabels: Record<string, string> = {
    no_data_penalty: "No data available",
    missing_values_penalty: "Missing values",
    duplicate_rows_penalty: "Duplicate rows",
    potential_outliers_penalty: "Potential outliers",
  };

  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset =
    circumference -
    (safeScore / 100) * circumference;

  return (
    <div className="rounded-2xl border bg-card p-6 shadow-sm">

      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold">
          Data Quality Score
        </h2>

        <p className="mt-1 text-sm text-muted-foreground">
          Overall quality based on detected data issues.
        </p>
      </div>

      {/* Score */}
      <div className="mt-6 flex flex-col items-center gap-6 sm:flex-row">

        <div className="relative h-36 w-36 shrink-0">

          <svg
            className="h-full w-full -rotate-90"
            viewBox="0 0 128 128"
          >

            {/* Background */}
            <circle
              cx="64"
              cy="64"
              r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth="10"
              className="text-muted"
            />

            {/* Progress */}
            <circle
              cx="64"
              cy="64"
              r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className={`${status.ring} transition-all duration-700`}
            />

          </svg>

          <div className="absolute inset-0 flex flex-col items-center justify-center">

            <span className="text-3xl font-bold">
              {safeScore.toFixed(0)}
            </span>

            <span className="text-xs text-muted-foreground">
              / 100
            </span>

          </div>

        </div>

        {/* Status */}
        <div>

          <p className={`text-lg font-semibold ${status.text}`}>
            {status.label} dataset quality
          </p>

          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            {status.description}
          </p>

          {Object.keys(factors).length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {Object.entries(factors).map(([key, penalty]) => (
                <span
                  key={key}
                  className="rounded-full border border-border bg-muted/40 px-3 py-1 text-xs text-muted-foreground"
                >
                  {factorLabels[key] ?? key.replace(/_/g, " ")}:{" "}
                  {Number(penalty).toFixed(2)} points
                </span>
              ))}
            </div>
          )}

        </div>

      </div>

    </div>
  );
}