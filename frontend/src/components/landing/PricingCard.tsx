import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";

type PricingCardProps = {
  title: string;
  price: string;
  description: string;
  features: string[];
  featured?: boolean;
};

export default function PricingCard({
  title,
  price,
  description,
  features,
  featured = false,
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
        
      {/* Title */}
      <h3
        className={`text-2xl font-bold ${
          featured ? "text-white" : "text-slate-900 dark:text-white"
        }`}
      >
        {title}
      </h3>

      {/* Description */}
      <p
        className={`mt-2 ${
          featured
            ? "text-indigo-100"
            : "text-slate-600 dark:text-slate-300"
        }`}
      >
        {description}
      </p>

      {/* Price */}
      <div className="mt-8">
        <span
          className={`text-5xl font-bold ${
            featured ? "text-white" : "text-slate-900 dark:text-white"
          }`}
        >
          {price}
        </span>
      </div>

      {/* Features */}
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

      {/* Button */}
      <Button
    className={`mt-10 w-full ${
         featured
         ? "bg-white text-indigo-600 hover:bg-slate-100"
         : "bg-indigo-600 text-white hover:bg-indigo-700"
    }`}
     >
       Get Started
    </Button>
    </div>
  );
}