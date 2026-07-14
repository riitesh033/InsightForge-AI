type FeatureCardProps = {
  title: string;
  description: string;
  icon: React.ReactNode;
};

export default function FeatureCard({
  title,
  description,
  icon,
}: FeatureCardProps) {
  return (
    <div className="card rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-xl">
      <div className="mb-4 text-indigo-600">
        {icon}
      </div>

      <h3 className="mb-2 text-xl font-bold">
        {title}
      </h3>

      <p className="text-slate-600 dark:text-slate-300">
        {description}
      </p>
    </div>
  );
}