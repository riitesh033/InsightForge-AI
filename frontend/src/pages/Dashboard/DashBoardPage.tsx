import Charts from "@/components/dashboard/Charts";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import DashboardSkeleton from "@/components/dashboard/DashboardSkeleton";
import QuickActions from "@/components/dashboard/QuickActions";
import RecentAnalyses from "@/components/dashboard/RecentAnalyses";
import RecentDatasetsTable from "@/components/dashboard/RecentDatasetsTable";
import StatsGrid from "@/components/dashboard/StatsGrid";
import { useDashboard } from "@/hooks/useDashboard";

export default function DashboardPage() {
  const { data, loading, error } = useDashboard();

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-600">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-xl border p-8 text-center">
        No dashboard data available.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <DashboardHeader />

      <QuickActions />

      <StatsGrid stats={data.stats} />

      <Charts charts={data.charts} />

      <div className="grid gap-6 lg:grid-cols-2">
        <RecentDatasetsTable
          datasets={data.recent_datasets}
        />

        <RecentAnalyses
          analyses={data.recent_analyses}
        />
      </div>
    </div>
  );
}