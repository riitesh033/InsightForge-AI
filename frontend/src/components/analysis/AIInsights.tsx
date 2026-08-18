import {
  Sparkles,
  Lightbulb,
  Bot,
} from "lucide-react";

interface Props {
  summary: string;
}

export default function AIInsights({
  summary,
}: Props) {
  const hasInsights =
    typeof summary === "string" &&
    summary.trim().length > 0;

  const formattedSummary = hasInsights
    ? summary.trim()
    : "No AI insights are available for this dataset.";

  return (
    <div className="rounded-2xl border bg-card p-6 shadow-sm">

      {/* Header */}
      <div className="flex items-start gap-4">

        <div className="rounded-xl bg-primary/10 p-3">
          <Sparkles className="h-6 w-6 text-primary" />
        </div>

        <div className="flex-1">

          <div className="flex items-center gap-2">

            <h2 className="text-xl font-semibold">
              AI Generated Insights
            </h2>

            {hasInsights && (
              <span className="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
                AI Analysis
              </span>
            )}

          </div>

          <p className="mt-1 text-sm text-muted-foreground">
            Automated analysis and recommendations generated
            from your dataset.
          </p>

        </div>

      </div>

      {/* Content */}
      <div className="mt-6 rounded-xl border bg-muted/30 p-5">

        <div className="flex gap-4">

          <div className="mt-1 shrink-0">

            {hasInsights ? (
              <Lightbulb className="h-5 w-5 text-primary" />
            ) : (
              <Bot className="h-5 w-5 text-muted-foreground" />
            )}

          </div>

          <div className="min-w-0 flex-1">

            {hasInsights ? (
              <div className="whitespace-pre-line text-sm leading-7">
                {formattedSummary}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                {formattedSummary}
              </p>
            )}

          </div>

        </div>

      </div>

      {/* Footer */}
      {hasInsights && (
        <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">

          <Sparkles className="h-3.5 w-3.5" />

          <span>
            Generated automatically from the analyzed dataset.
          </span>

        </div>
      )}

    </div>
  );
}