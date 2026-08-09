import {
  Database,
  Columns3,
  Rows3,
  AlertTriangle,
} from "lucide-react";

interface MissingValueInfo {
  count: number;
  percent: number;
}

interface DuplicateInfo {
  count: number;
  [key: string]: any;
}

interface Props {
  summary: Record<string, any>;
  missingValues: Record<string, MissingValueInfo>;
  duplicates: DuplicateInfo;
}

export default function AnalysisStats({
  summary,
  missingValues,
  duplicates,
}: Props) {
  const totalRows = Number(summary.rows ?? 0);

  const totalColumns = Number(summary.columns ?? 0);

  const missingCount = Object.values(missingValues).reduce(
    (total, value) => total + Number(value.count ?? 0),
    0
  );

  const duplicateCount = Number(duplicates.count ?? 0);

  const cards = [
    {
      title: "Total Rows",
      value: totalRows.toLocaleString(),
      icon: Rows3,
    },
    {
      title: "Columns",
      value: totalColumns,
      icon: Columns3,
    },
    {
      title: "Missing Values",
      value: missingCount,
      icon: AlertTriangle,
    },
    {
      title: "Duplicates",
      value: duplicateCount,
      icon: Database,
    },
  ];

  return (
    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;

        return (
          <div
            key={card.title}
            className="rounded-2xl border bg-card p-6 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  {card.title}
                </p>

                <h2 className="mt-2 text-3xl font-bold">
                  {card.value}
                </h2>
              </div>

              <div className="rounded-xl bg-primary/10 p-3">
                <Icon className="h-6 w-6 text-primary" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

