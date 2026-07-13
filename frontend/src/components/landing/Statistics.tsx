import StatCard from "./StatCard";

const stats = [
  {
    value: "10K+",
    label: "Datasets Analyzed",
  },
  {
    value: "98%",
    label: "AI Accuracy",
  },
  {
    value: "50+",
    label: "Interactive Charts",
  },
  {
    value: "24/7",
    label: "AI Assistant",
  },
];

export default function Statistics() {
  return (
    <section className="bg-slate-900 py-28 text-white">

      <div className="mx-auto max-w-7xl px-6">

        <div className="mb-16 text-center">

          <h2 className="text-4xl font-bold">

            Trusted by Future Data Professionals

          </h2>

          <p className="mt-4 text-slate-300">

            Built to simplify data analysis with the power of AI.

          </p>

        </div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">

          {stats.map((stat) => (
            <StatCard
              key={stat.label}
              value={stat.value}
              label={stat.label}
            />
          ))}

        </div>

      </div>

    </section>
  );
}