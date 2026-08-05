import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface QualityDistribution {
  range: string;
  count: number;
}

interface Props {
  data: QualityDistribution[];
}

export default function QualityBarChart({
  data,
}: Props) {
  return (
    <div className="rounded-2xl border bg-card p-6 shadow-sm">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">
          Quality Distribution
        </h2>

        <p className="text-sm text-muted-foreground">
          Dataset quality scores
        </p>
      </div>

      {data.length === 0 ? (
        <div className="flex h-[300px] items-center justify-center text-muted-foreground">
          No quality data available.
        </div>
      ) : (
        <ResponsiveContainer
          width="100%"
          height={300}
        >
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="range" />

            <YAxis allowDecimals={false} />

            <Tooltip />

            <Bar
              dataKey="count"
              radius={[8, 8, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}