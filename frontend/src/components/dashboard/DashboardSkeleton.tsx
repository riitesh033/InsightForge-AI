import Skeleton from "@/components/common/Skeleton";

export default function DashboardSkeleton() {
  return (
    <div className="space-y-6">

      <Skeleton className="h-10 w-72" />

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">

        <Skeleton className="h-40" />
        <Skeleton className="h-40" />
        <Skeleton className="h-40" />
        <Skeleton className="h-40" />

      </div>

      <Skeleton className="h-80" />

    </div>
  );
}