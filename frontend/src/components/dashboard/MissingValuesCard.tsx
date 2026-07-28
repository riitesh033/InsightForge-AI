interface Props {
  missingValues: Record<
    string,
    {
      count: number;
      percent: number;
    }
  >;
}

export default function MissingValuesCard({
  missingValues,
}: Props) {
  return (
    <div className="rounded-xl border border-border bg-card shadow-sm">

      <div className="border-b border-border p-6">

        <h2 className="text-xl font-semibold">
          Missing Values
        </h2>

      </div>

      <div className="space-y-5 p-6">

        {Object.entries(missingValues).map(
          ([column, value]) => {

            let color =
              "bg-green-500";

            if (value.percent > 50)
              color = "bg-red-500";
            else if (value.percent > 20)
              color = "bg-orange-500";
            else if (value.percent > 0)
              color = "bg-yellow-500";

            return (
              <div key={column}>

                <div className="mb-2 flex justify-between">

                  <span className="font-medium">
                    {column}
                  </span>

                  <span className="text-sm text-muted-foreground">

                    {value.count} ({value.percent}%)

                  </span>

                </div>

                <div className="h-3 rounded-full bg-muted">

                  <div
                    className={`${color} h-3 rounded-full`}
                    style={{
                      width: `${value.percent}%`,
                    }}
                  />

                </div>

              </div>
            );
          }
        )}

      </div>

    </div>
  );
}