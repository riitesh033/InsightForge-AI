interface StepCardProps {
  number: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}

export default function StepCard({
  number,
  title,
  description,
  icon,
}: StepCardProps) {
  return (
    <div className="relative card rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 shadow-sm transition-all duration-300 hover:-translate-y-2 hover:shadow-xl">

      <div className="absolute -top-4 left-6 flex h-10 w-10 items-center justify-center rounded-full bg-indigo-600 text-sm font-bold text-white">
        {number}
      </div>

      <div className="mb-6 mt-4 text-indigo-600">
        {icon}
      </div>

      <h3 className="mb-3 text-xl font-bold">
        {title}
      </h3>

      <p className="text-slate-600 dark:text-slate-300">
        {description}
      </p>

    </div>
  );
}