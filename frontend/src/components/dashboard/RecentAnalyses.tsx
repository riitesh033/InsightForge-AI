import { format } from "date-fns";
import { RecentAnalysis } from "@/services/dashboard";

interface Props {
  analyses: RecentAnalysis[];
}

export default function RecentAnalyses({
  analyses,
}: Props) {
  return (
    <div className="rounded-2xl border bg-card shadow-sm">
      <div className="border-b p-5">
        <h2 className="text-lg font-semibold">
          Recent Analyses
        </h2>
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
              className="flex items-center justify-between p-5"
            >
              <div>
                <h3 className="font-medium">
                  {analysis.dataset_name}
                </h3>

                <p className="text-sm text-muted-foreground">
                  {format(
                    new Date(analysis.created_at),
                    "dd MMM yyyy"
                  )}
                </p>
              </div>

              <span className="rounded-full bg-green-100px-3 py-1 text-sm font-medium text-green-700 dark:bg-green-900 dark:text-green-300">
                {analysis.quality_score}%
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}