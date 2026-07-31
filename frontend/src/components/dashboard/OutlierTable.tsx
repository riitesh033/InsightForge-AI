interface Props {
  outliers: Record<string, number>;
}

export default function OutlierTable({
  outliers,
}: Props) {
  return (
    <div className="rounded-xl border border-border bg-card shadow-sm">

      <div className="border-b border-border p-6">

        <h2 className="text-xl font-semibold">
          Outliers
        </h2>

      </div>

      <div className="p-6 space-y-4">

        {Object.entries(outliers).map(
          ([column, count]) => (

            <div
              key={column}
              className="flex justify-between rounded-lg border p-4"
            >

              <span>{column}</span>

              <span className="font-bold">
                {count}
              </span>

            </div>

          )
        )}

      </div>

    </div>
  );
}