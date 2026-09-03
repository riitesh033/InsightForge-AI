import { format } from "date-fns";
import { useNavigate } from "react-router-dom";

import { RecentAnalysis } from "@/services/dashboard";

interface Props {
  analyses: RecentAnalysis[];
}

export default function RecentAnalyses({
  analyses,
}: Props) {
  const navigate = useNavigate();

  function handleAnalysisClick(datasetId: number) {
    navigate(`/dashboard/analysis/${datasetId}`);
  }

  return (
    <div className="rounded-2xl border bg-card shadow-sm">
      <div className="border-b p-5">
        <h2 className="text-lg font-semibold">
          Recent Analyses
        </h2>

        <p className="mt-1 text-sm text-muted-foreground">
          Recently generated dataset analyses
        </p>
      </div>

      <div className="divide-y">
        {analyses.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No analyses available.
          </div>
        ) : (
          analyses.map((analysis) => (
            <div
              key={analysis.analysis_id}
              onClick={() =>
                handleAnalysisClick(analysis.dataset_id)
              }
              className="flex cursor-pointer items-center justify-between p-5 transition-colors hover:bg-muted/40"
            >
              <div className="min-w-0">
                <h3 className="truncate font-medium">
                  {analysis.dataset_name}
                </h3>

                <p className="mt-1 text-sm text-muted-foreground">
                  Analyzed{" "}
                  {format(
                    new Date(analysis.created_at),
                    "dd MMM yyyy"
                  )}
                </p>
              </div>

              <span className="ml-4 shrink-0 rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-700 dark:bg-green-900 dark:text-green-300">
                {analysis.quality_score}%
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}