import PlanCatalog from "@/components/payments/PlanCatalog";

export default function Pricing() {
  return (
    <section id="pricing" className="bg-slate-50 py-20 dark:bg-slate-900 sm:py-28">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <div className="mb-12 text-center sm:mb-16">
          <span className="inline-block rounded-full bg-indigo-100 px-4 py-2 text-sm font-semibold text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
            Pricing
          </span>
          <h2 className="mt-6 text-3xl font-bold text-slate-900 dark:text-white sm:text-4xl">
            Simple Pricing
          </h2>
          <p className="mt-4 text-base text-slate-600 dark:text-slate-400 sm:text-lg">
            Choose the plan that fits your needs.
          </p>
        </div>

        <PlanCatalog />
      </div>
    </section>
  );
}
