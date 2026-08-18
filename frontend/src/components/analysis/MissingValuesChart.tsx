import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

interface MissingValueInfo {
  count: number;
  percent: number;
}

interface Props {
  missingValues: Record<string, MissingValueInfo>;
}

export default function MissingValuesChart({
  missingValues,
}: Props) {
  const data = Object.entries(missingValues)
    .filter(([, value]) => value.count > 0)
    .sort(([, a], [, b]) => b.percent - a.percent)
    .map(([name, value]) => ({
      name,
      missing: value.percent,
      count: value.count,
    }));

  return (
    <div className="rounded-xl border bg-card p-6 shadow-sm">

      {/* Header */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold">
          Missing Values
        </h2>

        <p className="text-sm text-muted-foreground">
          Columns containing missing data
        </p>
      </div>

      {/* No missing values */}
      {data.length === 0 ? (
        <div className="flex h-[300px] flex-col items-center justify-center text-center">
          <div className="mb-2 text-4xl">
            ✓
          </div>

          <p className="font-medium">
            No missing values
          </p>

          <p className="text-sm text-muted-foreground">
            All columns are complete.
          </p>
        </div>
      ) : (
        <div className="h-[300px] w-full">

          <ResponsiveContainer
            width="100%"
            height="100%"
          >
            <BarChart
              data={data}
              margin={{
                top: 10,
                right: 10,
                left: 0,
                bottom: 60,
              }}
            >

              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
              />

              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                interval={0}
                height={80}
              />

              <YAxis
                domain={[0, 100]}
                tickFormatter={(value) => `${value}%`}
              />

              <Tooltip
                formatter={(value, name, props) => {
                  if (name === "Missing") {
                    return [
                      `${Number(value).toFixed(2)}%`,
                      `Missing (${props.payload.count} values)`,
                    ];
                  }

                  return [value, name];
                }}
              />

              <Bar
                dataKey="missing"
                name="Missing"
                radius={[6, 6, 0, 0]}
              />

            </BarChart>
          </ResponsiveContainer>

        </div>
      )}

    </div>
  );
}