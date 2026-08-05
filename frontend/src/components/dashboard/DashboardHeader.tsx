import { CalendarDays } from "lucide-react";

export default function DashboardHeader() {
  const today = new Date();

  return (
    <div className="flex flex-col justify-between gap-4 rounded-2xl border bg-card p-6 shadow-sm md:flex-row md:items-center">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Dashboard
        </h1>

        <p className="mt-2 text-muted-foreground">
          Welcome back! Here's an overview of your datasets and analyses.
        </p>
      </div>

      <div className="flex items-center gap-2 rounded-xl border bg-muted/40 px-4 py-2 text-sm">
        <CalendarDays className="h-4 w-4" />

        {today.toLocaleDateString(undefined, {
          weekday: "long",
          day: "numeric",
          month: "long",
          year: "numeric",
        })}
      </div>
    </div>
  );
}