interface Props {
  summary: string;
}

export default function AISummaryCard({
  summary,
}: Props) {
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <h2 className="mb-4 text-xl font-semibold text-foreground">
        AI Dataset Summary
      </h2>

      <p className="leading-7 text-muted-foreground">
        {summary}
      </p>
    </div>
  );
}