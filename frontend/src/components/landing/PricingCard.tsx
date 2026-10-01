import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PricingCardProps {
  title: string;
  price: string;
  features: string[];
  isFree: boolean;
  featured?: boolean;
  loading?: boolean;
  disabled?: boolean;
  buttonLabel?: string;
  onSelect: () => void;
}

export default function PricingCard({
  title,
  price,
  features,
  isFree,
  featured = false,
  loading = false,
  disabled = false,
  buttonLabel,
  onSelect,
}: PricingCardProps) {
  return (
    <div
      className={`rounded-3xl border p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-xl ${
        featured
          ? "border-indigo-600 bg-indigo-600 text-white shadow-lg dark:bg-indigo-700"
          : "border-slate-200 bg-white text-slate-900 dark:border-slate-800 dark:bg-slate-900 dark:text-white"
      }`}
    >
      {featured && (
        <div className="mb-6 inline-block rounded-full bg-white/20 px-4 py-1 text-sm font-semibold text-white">
          Most Popular
        </div>
      )}

      <h3 className="break-words text-2xl font-bold">{title}</h3>

      <div className="mt-8">
        <span className="break-words text-4xl font-bold sm:text-5xl">
          {price}
        </span>
      </div>

      <ul className="mt-8 space-y-4">
        {features.map((feature) => (
          <li
            key={feature}
            className={`flex items-center gap-3 ${
              featured ? "text-white" : "text-slate-700 dark:text-slate-300"
            }`}
          >
            <Check size={18} className="text-green-500" />
            {feature}
          </li>
        ))}
      </ul>

      <Button
        type="button"
        onClick={onSelect}
        disabled={disabled}
        aria-busy={loading}
        className={`mt-10 w-full ${
          featured
            ? "bg-white text-indigo-600 hover:bg-slate-100"
            : "bg-indigo-600 text-white hover:bg-indigo-700"
        }`}
      >
        {buttonLabel ??
          (loading
        ? "Redirecting..."
        : isFree
          ? "Get Started"
          : "Choose Plan")}
      </Button>
    </div>
  );
}
