interface StatCardProps {
  value: string;
  label: string;
}

export default function StatCard({
  value,
  label,
}: StatCardProps) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm transition-all duration-300 hover:-translate-y-2 hover:shadow-xl">

      <h3 className="text-5xl font-extrabold text-indigo-600">
        {value}
      </h3>

      <p className="mt-4 text-slate-600">
        {label}
      </p>

    </div>
  );
}