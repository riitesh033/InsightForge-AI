import FAQItem from "./FAQItem";

const faqs = [
  {
    question: "Which file formats are supported?",
    answer:
      "InsightForge AI currently supports CSV and Excel (.xlsx) datasets.",
  },
  {
    question: "Can I generate PDF reports?",
    answer:
      "Yes. After analysis, you can download detailed AI-generated PDF reports.",
  },
  {
    question: "Does the application clean datasets?",
    answer:
      "Yes. It identifies missing values, duplicates, outliers, and inconsistent data types.",
  },
  {
    question: "Is my uploaded data secure?",
    answer:
      "Yes. Uploaded datasets are processed securely, and user authentication is protected with JWT.",
  },
  {
    question: "Can I chat with my dataset?",
    answer:
      "Yes. The AI Chat module allows you to ask questions about your uploaded dataset using natural language.",
  },
];

export default function FAQ() {
  return (
    <section id="faq" className="bg-white dark:bg-slate-950">
      <div className="mx-auto max-w-4xl px-6">

        <div className="mb-16 text-center">

          <h2 className="text-4xl font-bold">
            Frequently Asked Questions
          </h2>

          <p className="mt-4 text-slate-600">
            Everything you need to know about InsightForge AI.
          </p>

        </div>

        <div className="space-y-5">

          {faqs.map((faq) => (
            <FAQItem
              key={faq.question}
              {...faq}
            />
          ))}

        </div>

      </div>
    </section>
  );
}