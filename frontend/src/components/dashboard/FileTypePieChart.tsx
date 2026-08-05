import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface FileTypeDistribution {
  file_type: string;
  count: number;
}

interface Props {
  data: FileTypeDistribution[];
}

const COLORS = [
  "#2563eb",
  "#16a34a",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
];

export default function FileTypePieChart({
  data,
}: Props) {
  return (
    <div className="rounded-2xl border bg-card p-6 shadow-sm">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">
          File Types
        </h2>

        <p className="text-sm text-muted-foreground">
          Uploaded dataset formats
        </p>
      </div>

      {data.length === 0 ? (
        <div className="flex h-[300px] items-center justify-center text-muted-foreground">
          No file type data available.
        </div>
      ) : (
        <ResponsiveContainer
          width="100%"
          height={300}
        >
          <PieChart>
            <Pie
              data={data}
              dataKey="count"
              nameKey="file_type"
              outerRadius={90}
              label
            >
              {data.map((_, index) => (
                <Cell
                  key={index}
                  fill={
                    COLORS[index % COLORS.length]
                  }
                />
              ))}
            </Pie>

            <Tooltip />

            <Legend />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}