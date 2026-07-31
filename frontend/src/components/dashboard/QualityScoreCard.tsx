interface Props {
  score: number;
}

export default function QualityScoreCard({
  score,
}: Props) {
  const color =
    score >= 90
      ? "text-green-600"
      : score >= 70
      ? "text-yellow-500"
      : "text-red-500";

  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">

      <h2 className="text-xl font-semibold">
        Dataset Quality
      </h2>

      <div className="mt-6 flex items-center justify-center">

        <div
          className={`text-6xl font-bold ${color}`}
        >
          {score}
        </div>

        <span className="ml-2 text-3xl">
          /100
        </span>

      </div>

    </div>
  );
}