import PricingCard from "./PricingCard";

const plans = [
  {
    title: "Student",
    price: "Free",
    description: "Perfect for students and learning.",
    features: [
      "CSV Upload",
      "Excel Upload",
      "Basic AI Analysis",
      "Dashboard",
      "PDF Report",
    ],
  },

  {
    title: "Professional",
    price: "$19",
    description: "Designed for analysts and businesses.",
    featured: true,
    features: [
      "Unlimited Uploads",
      "Advanced AI Insights",
      "Forecasting",
      "AI Chat",
      "Priority Support",
    ],
  },

  {
    title: "Enterprise",
    price: "Custom",
    description: "For teams and organizations.",
    features: [
      "Everything in Pro",
      "Custom AI Models",
      "API Access",
      "Team Collaboration",
      "Dedicated Support",
    ],
  },
];

export default function Pricing() {
  return (
    <section
      id="pricing"
      className="bg-slate-50 py-28 dark:bg-slate-900"
    >
      <div className="mx-auto max-w-7xl px-6">

        {/* Heading */}

        <div className="mb-16 text-center">

          <span className="inline-block rounded-full bg-indigo-100 px-4 py-2 text-sm font-semibold text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
            Pricing
          </span>

          <h2 className="mt-6 text-4xl font-bold text-slate-900 dark:text-white">
            Simple Pricing
          </h2>

          <p className="mt-4 text-lg text-slate-600 dark:text-slate-400">
            Flexible plans for students, professionals and organizations.
          </p>

        </div>

        {/* Cards */}

        <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-3">

          {plans.map((plan) => (
            <PricingCard
              key={plan.title}
              {...plan}
            />
          ))}

        </div>

      </div>
    </section>
  );
}