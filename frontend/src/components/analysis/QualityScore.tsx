interface Props {
  score: number;
}

export default function QualityScore({
  score,
}: Props) {
  const safeScore = Math.max(
    0,
    Math.min(100, Number(score) || 0)
  );

  const getStatus = () => {
    if (safeScore >= 80) {
      return {
        label: "Excellent",
        description:
          "Your dataset has very few quality issues.",
        text: "text-green-600 dark:text-green-400",
        ring: "text-green-500",
      };
    }

    if (safeScore >= 50) {
      return {
        label: "Needs Improvement",
        description:
          "Some data quality issues should be reviewed.",
        text: "text-yellow-600 dark:text-yellow-400",
        ring: "text-yellow-500",
      };
    }

    return {
      label: "Poor",
      description:
        "The dataset contains significant quality issues.",
      text: "text-red-600 dark:text-red-400",
      ring: "text-red-500",
    };
  };

  const status = getStatus();

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

        </div>

      </div>

    </div>
  );
}