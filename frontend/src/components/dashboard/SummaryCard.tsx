interface Props {
  title: string;
  value: string | number;
}

export default function SummaryCard({
  title,
  value,
}: Props) {
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm transition hover:shadow-md">
      <p className="text-sm text-muted-foreground">
        {title}
      </p>

      <h2 className="mt-3 text-3xl font-bold text-foreground">
        {value}
      </h2>
    </div>
  );
}