import {
  Database,
  FileBarChart,
  Star,
  Table2,
} from "lucide-react";

import StatsCard from "./StatsCard";

interface Props {
  stats: {
    total_datasets: number;
    total_analyses: number;
    average_quality_score: number;
    total_rows: number;
  };
}

export default function StatsGrid({
  stats,
}: Props) {
  return (
    <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
      <StatsCard
        title="Datasets"
        value={stats.total_datasets}
        icon={<Database className="h-6 w-6" />}
      />

      <StatsCard
        title="Analyses"
        value={stats.total_analyses}
        icon={<FileBarChart className="h-6 w-6" />}
      />

      <StatsCard
        title="Average Quality"
        value={`${stats.average_quality_score}%`}
        icon={<Star className="h-6 w-6" />}
      />

      <StatsCard
        title="Rows"
        value={stats.total_rows.toLocaleString()}
        icon={<Table2 className="h-6 w-6" />}
      />
    </div>
  );
}