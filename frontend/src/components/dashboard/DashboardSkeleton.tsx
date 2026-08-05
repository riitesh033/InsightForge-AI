export default function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-24 rounded-2xl bg-muted" />

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {[1, 2, 3, 4].map((item) => (
          <div
            key={item}
            className="h-32 rounded-2xl bg-muted"
          />
        ))}
      </div>

      <div className="h-80 rounded-2xl bg-muted" />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="h-96 rounded-2xl bg-muted" />
        <div className="h-96 rounded-2xl bg-muted" />
      </div>
    </div>
  );
}