import StatsGrid from "@/components/dashboard/StatsGrid";
import { useDashboard } from "@/hooks/useDashboard";

export default function DashboardPage() {
  const {
    data,
    loading,
    error,
  } = useDashboard();

  if (loading)
    return <div className="p-8">Loading...</div>;

  if (error)
    return (
      <div className="p-8 text-red-500">
        {error}
      </div>
    );

  if (!data)
    return (
      <div className="p-8">
        No dashboard data.
      </div>
    );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">
          Dashboard
        </h1>

        <p className="text-muted-foreground">
          Welcome back!
        </p>
      </div>

      <StatsGrid stats={data.stats} />
    </div>
  );
}