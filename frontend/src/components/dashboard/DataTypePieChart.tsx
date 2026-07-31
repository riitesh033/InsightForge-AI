import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface ColumnInfo {
  dtype: string;
}

interface Props {
  columns: ColumnInfo[];
}

const COLORS = [
  "#3B82F6",
  "#22C55E",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#14B8A6",
];

export default function DataTypePieChart({
  columns,
}: Props) {
  const counts: Record<string, number> = {};

  columns.forEach((column) => {
    counts[column.dtype] =
      (counts[column.dtype] || 0) + 1;
  });

  const data = Object.entries(counts).map(
    ([name, value]) => ({
      name,
      value,
    })
  );

  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">

      <h2 className="mb-6 text-xl font-semibold">
        Data Types
      </h2>

      <ResponsiveContainer
        width="100%"
        height={350}
      >

        <PieChart>

          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            outerRadius={120}
            label
          >

            {data.map((_, index) => (

              <Cell
                key={index}
                fill={
                  COLORS[
                    index % COLORS.length
                  ]
                }
              />

            ))}

          </Pie>

          <Tooltip />

        </PieChart>

      </ResponsiveContainer>

    </div>
  );
}