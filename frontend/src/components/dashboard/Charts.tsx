import FileTypePieChart from "./FileTypePieChart";
import QualityBarChart from "./QualityBarChart";
import UploadTrendChart from "./UploadTrendChart";

interface Props {
  charts: {
    uploads_per_month: {
      month: string;
      uploads: number;
    }[];

    file_types: {
      file_type: string;
      count: number;
    }[];

    quality_distribution: {
      range: string;
      count: number;
    }[];
  };
}

export default function Charts({
  charts,
}: Props) {
  return (
    <div className="grid gap-6">
      <UploadTrendChart
        data={charts.uploads_per_month}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <FileTypePieChart
          data={charts.file_types}
        />

        <QualityBarChart
          data={
            charts.quality_distribution
          }
        />
      </div>
    </div>
  );
}