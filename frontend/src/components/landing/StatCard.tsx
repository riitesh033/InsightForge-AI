interface StatCardProps {
  value: string;
  label: string;
}

export default function StatCard({
  value,
  label,
}: StatCardProps) {
  return (
    <div className="card rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 text-center shadow-sm transition-all duration-300 hover:-translate-y-2 hover:shadow-xl">

      <h3 className="text-5xl font-extrabold text-indigo-600">
        {value}
      </h3>

      <p className="mt-4 text-slate-600 dark:text-slate-300">
        {label}
      </p>

    </div>
  );
}