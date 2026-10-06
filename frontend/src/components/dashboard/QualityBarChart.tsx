import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useTheme } from "@/context/ThemeContext";

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
  const { theme } = useTheme();
  const chartColors =
    theme === "dark"
      ? {
          text: "#f8fafc",
          mutedText: "#94a3b8",
          grid: "#334155",
          surface: "#0f172a",
          border: "#334155",
        }
      : {
          text: "#0f172a",
          mutedText: "#64748b",
          grid: "#e2e8f0",
          surface: "#ffffff",
          border: "#e2e8f0",
        };

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
            <CartesianGrid
              stroke={chartColors.grid}
              strokeDasharray="3 3"
            />

            <XAxis
              dataKey="range"
              tick={{ fill: chartColors.mutedText }}
              tickLine={{ stroke: chartColors.grid }}
              axisLine={{ stroke: chartColors.grid }}
            />

            <YAxis
              allowDecimals={false}
              tick={{ fill: chartColors.mutedText }}
              tickLine={{ stroke: chartColors.grid }}
              axisLine={{ stroke: chartColors.grid }}
            />

            <Tooltip
              cursor={{ fill: chartColors.grid, fillOpacity: 0.2 }}
              contentStyle={{
                backgroundColor: chartColors.surface,
                border: `1px solid ${chartColors.border}`,
                borderRadius: "0.75rem",
                boxShadow: "0 10px 25px rgba(15, 23, 42, 0.16)",
                color: chartColors.text,
              }}
              labelStyle={{ color: chartColors.text }}
              itemStyle={{ color: chartColors.text }}
            />

            <Bar
              dataKey="count"
              fill="#6366f1"
              radius={[8, 8, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}