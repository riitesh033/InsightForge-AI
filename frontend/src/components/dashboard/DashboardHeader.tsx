import { CalendarDays } from "lucide-react";

export default function DashboardHeader() {
  const today = new Date();

  return (
    <section className="relative overflow-hidden rounded-[28px] border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.22),transparent_34%),linear-gradient(135deg,rgba(15,23,42,0.95),rgba(17,24,39,0.9))] p-6 shadow-[0_30px_80px_rgba(15,23,42,0.45)] md:p-8">
      <div className="flex flex-col justify-between gap-6 md:flex-row md:items-center">
        <div className="max-w-2xl">
          <span className="inline-flex items-center gap-2 rounded-full border border-indigo-400/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-indigo-200">
            Overview
          </span>

          <h1 className="mt-4 text-3xl font-bold tracking-tight text-white md:text-4xl">
            Dashboard
          </h1>

          <p className="mt-3 max-w-xl text-sm text-slate-300 md:text-base">
            Welcome back! Here&apos;s an overview of your datasets, analyses, and AI insights.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start rounded-full border border-white/10 bg-slate-900/60 px-4 py-2 text-sm text-slate-200 shadow-lg shadow-slate-950/30 md:self-center">
          <CalendarDays className="h-4 w-4 text-indigo-300" />
          <span>
            {today.toLocaleDateString(undefined, {
              weekday: "long",
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </span>
        </div>
      </div>
    </section>
  );
}