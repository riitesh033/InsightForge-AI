import { useState } from "react";
import { ChevronDown } from "lucide-react";

type FAQItemProps = {
  question: string;
  answer: string;
};

export default function FAQItem({
  question,
  answer,
}: FAQItemProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white transition-all duration-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900">

      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between p-6 text-left"
      >
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          {question}
        </h3>

        <ChevronDown
          className={`text-slate-500 transition-transform duration-300 dark:text-slate-300 ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      <div
        className={`overflow-hidden transition-all duration-300 ${
          open ? "max-h-40 px-6 pb-6" : "max-h-0"
        }`}
      >
        <p className="leading-7 text-slate-600 dark:text-slate-300">
          {answer}
        </p>
      </div>

    </div>
  );
}