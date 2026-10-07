import {
  Database,
  Columns3,
  Rows3,
  AlertTriangle,
  ScanSearch,
} from "lucide-react";

interface MissingValueInfo {
  count: number;
  percent: number;
}

interface DuplicateInfo {
  count: number;
  percent?: number;
}

interface Props {
  summary: Record<string, unknown>;
  missingValues: Record<string, MissingValueInfo>;
  duplicates: DuplicateInfo;
  potentialOutliers?: number;
}

export default function AnalysisStats({
  summary,
  missingValues,
  duplicates,
  potentialOutliers = 0,
}: Props) {
  const totalRows = Number(summary?.rows ?? 0);

  const totalColumns = Number(summary?.columns ?? 0);

  const missingCount = Object.values(
    missingValues ?? {}
  ).reduce(
    (total, value) =>
      total + Number(value?.count ?? 0),
    0
  );

  const duplicateCount = Number(
    duplicates?.count ?? 0
  );

  const missingPercent =
    totalRows > 0 && totalColumns > 0
      ? (missingCount / (totalRows * totalColumns)) *
        100
      : 0;

  const duplicatePercent =
    Number(duplicates?.percent ?? 0);

  const cards = [
    {
      title: "Total Rows",
      value: totalRows.toLocaleString(),
      description: "Records in dataset",
      icon: Rows3,
    },
    {
      title: "Columns",
      value: totalColumns.toLocaleString(),
      description: "Variables analyzed",
      icon: Columns3,
    },
    {
      title: "Missing Values",
      value: missingCount.toLocaleString(),
      description:
        missingCount > 0
          ? `${missingPercent.toFixed(2)}% of all cells`
          : "No missing cells",
      icon: AlertTriangle,
    },
    {
      title: "Duplicates",
      value: duplicateCount.toLocaleString(),
      description:
        duplicateCount > 0
          ? duplicatePercent > 0
            ? `${duplicatePercent.toFixed(2)}% of rows`
            : "Duplicate rows detected"
          : "No duplicate rows",
      icon: Database,
    },
    {
      title: "Potential Outliers",
      value: potentialOutliers.toLocaleString(),
      description: "IQR flags across numeric columns",
      icon: ScanSearch,
    },
  ];

  return (
    <div className="grid min-w-0 gap-5 sm:grid-cols-2 xl:grid-cols-5">

      {cards.map((card) => {
        const Icon = card.icon;

        return (
          <div
            key={card.title}
            className="min-w-0 overflow-hidden rounded-2xl border border-border/70 bg-card p-5 shadow-sm transition-shadow hover:shadow-md"
          >

            <div className="flex min-w-0 items-start justify-between gap-3">

              <div className="min-w-0">

                <p className="text-sm font-medium text-muted-foreground">
                  {card.title}
                </p>

                <h2 className="mt-2 break-words text-2xl font-bold tracking-tight 2xl:text-3xl">
                  {card.value}
                </h2>

                <p className="mt-2 text-xs text-muted-foreground">
                  {card.description}
                </p>

              </div>

              <div className="shrink-0 rounded-xl bg-primary/10 p-3">
                <Icon className="h-6 w-6 text-primary" />
              </div>

            </div>

          </div>
        );
      })}

    </div>
  );
}