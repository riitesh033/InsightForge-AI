import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Props {
  missingValues: Record<
    string,
    {
      count: number;
      percent: number;
    }
  >;
}

export default function MissingValuesChart({
  missingValues,
}: Props) {
  const data = Object.entries(
    missingValues
  ).map(([column, value]) => ({
    column,
    missing: value.count,
  }));

  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">

      <h2 className="mb-6 text-xl font-semibold">
        Missing Values Chart
      </h2>

      <ResponsiveContainer
        width="100%"
        height={350}
      >

        <BarChart data={data}>

          <CartesianGrid strokeDasharray="3 3" />

          <XAxis dataKey="column" />

          <YAxis />

          <Tooltip />

          <Bar
            dataKey="missing"
            radius={[6, 6, 0, 0]}
          />

        </BarChart>

      </ResponsiveContainer>

    </div>
  );
}