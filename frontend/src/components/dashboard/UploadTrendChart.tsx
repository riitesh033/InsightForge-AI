import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface UploadTrend {
  month: string;
  uploads: number;
}

interface Props {
  data: UploadTrend[];
}

export default function UploadTrendChart({ data }: Props) {
  return (
    <div className="rounded-2xl border bg-card p-6 shadow-sm">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">
          Upload Trend
        </h2>

        <p className="text-sm text-muted-foreground">
          Dataset uploads by month
        </p>
      </div>

      {data.length === 0 ? (
        <div className="flex h-[300px] items-center justify-center text-muted-foreground">
          No upload data available.
        </div>
      ) : (
        <ResponsiveContainer
          width="100%"
          height={300}
        >
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="month" />

            <YAxis allowDecimals={false} />

            <Tooltip />

            <Line
              type="monotone"
              dataKey="uploads"
              strokeWidth={3}
              dot={{ r: 5 }}
              activeDot={{ r: 7 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}