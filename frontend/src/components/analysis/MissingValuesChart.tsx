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
  const allData = Object.entries(missingValues)
    .filter(([, value]) => value.count > 0)
    .sort(([, a], [, b]) => b.percent - a.percent)
    .map(([name, value]) => ({
      name,
      missing: value.percent,
      count: value.count,
    }));

  // Keep the chart readable when a dataset contains many columns.
  const data = allData.slice(0, 15);

  return (
    <div className="rounded-2xl border border-border/70 bg-card p-6 shadow-sm">
      <div className="mb-6">
        <h2 className="text-xl font-semibold">
          Missing Values
        </h2>

        <p className="mt-1 text-sm text-muted-foreground">
          {allData.length > 15
            ? `Top 15 of ${allData.length} columns by missing percentage`
            : "Columns containing missing data"}
        </p>
      </div>

      {data.length === 0 ? (
        <div className="flex h-[300px] flex-col items-center justify-center rounded-xl border border-border/60 bg-background/40 text-center">
          <div className="mb-2 text-4xl text-primary">
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
        <div className="h-[430px] w-full">
          <ResponsiveContainer
            width="100%"
            height="100%"
          >
            <BarChart
              data={data}
              layout="vertical"
              margin={{
                top: 8,
                right: 20,
                left: 12,
                bottom: 8,
              }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                horizontal={false}
                stroke="hsl(var(--border))"
              />

              <XAxis
                type="number"
                domain={[0, 100]}
                tickFormatter={(value) => `${value}%`}
                tick={{
                  fill: "hsl(var(--muted-foreground))",
                  fontSize: 12,
                }}
                axisLine={{
                  stroke: "hsl(var(--border))",
                }}
                tickLine={{
                  stroke: "hsl(var(--border))",
                }}
              />

              <YAxis
                type="category"
                dataKey="name"
                width={155}
                tick={{
                  fill: "hsl(var(--muted-foreground))",
                  fontSize: 11,
                }}
                axisLine={{
                  stroke: "hsl(var(--border))",
                }}
                tickLine={false}
              />

              <Tooltip
                cursor={{
                  fill: "hsl(var(--primary) / 0.08)",
                }}
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "12px",
                  color: "hsl(var(--foreground))",
                }}
                labelStyle={{
                  color: "hsl(var(--foreground))",
                  fontWeight: 600,
                }}
                itemStyle={{
                  color: "hsl(var(--primary))",
                }}
                formatter={(value, name, props) => {
                  if (name === "Missing") {
                    return [
                      `${Number(value).toFixed(2)}%`,
                      `Missing (${props.payload.count.toLocaleString()} values)`,
                    ];
                  }

                  return [value, name];
                }}
              />

              <Bar
                dataKey="missing"
                name="Missing"
                fill="hsl(var(--primary))"
                radius={[0, 6, 6, 0]}
                barSize={18}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
