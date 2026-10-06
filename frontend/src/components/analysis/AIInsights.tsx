import {
  Sparkles,
  Lightbulb,
  Bot,
  Loader2,
} from "lucide-react";

interface Props {
  summary: string;
  available?: boolean;
  loading?: boolean;
}

export default function AIInsights({
  summary,
  available = true,
  loading = false,
}: Props) {
  const hasInsights =
    typeof summary === "string" &&
    summary.trim().length > 0;

  const formattedSummary = hasInsights
    ? summary.trim()
    : "AI explanation is temporarily unavailable. Your deterministic dataset analysis is still available.";

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
              AI Insights
            </h2>

            {available && hasInsights && (
              <span className="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
                AI explanation
              </span>
            )}

          </div>

          <p className="mt-1 text-sm text-muted-foreground">
            Natural-language context generated from the verified dataset profile.
          </p>

        </div>

      </div>

      {/* Content */}
      <div className="mt-6 rounded-xl border bg-muted/30 p-5">

        <div className="flex gap-4">

          <div className="mt-1 shrink-0">

            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
            ) : hasInsights && available ? (
              <Lightbulb className="h-5 w-5 text-primary" />
            ) : (
              <Bot className="h-5 w-5 text-muted-foreground" />
            )}

          </div>

          <div className="min-w-0 flex-1">

            {loading ? (
              <p className="text-sm text-muted-foreground">
                Preparing an explanation from the verified profile...
              </p>
            ) : hasInsights && available ? (
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
      {hasInsights && available && !loading && (
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