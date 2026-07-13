import StepCard from "./StepCard";

import {
  Upload,
  BrainCircuit,
  BarChart3,
  FileDown,
  ArrowRight,
} from "lucide-react";

const steps = [
  {
    number: "01",
    title: "Upload Dataset",
    description:
      "Upload CSV or Excel files securely with a simple drag-and-drop interface.",
    icon: <Upload size={42} />,
  },
  {
    number: "02",
    title: "AI Processing",
    description:
      "InsightForge AI automatically cleans, validates, and analyzes your dataset.",
    icon: <BrainCircuit size={42} />,
  },
  {
    number: "03",
    title: "Interactive Dashboard",
    description:
      "Visualize trends, correlations, missing values, and anomalies instantly.",
    icon: <BarChart3 size={42} />,
  },
  {
    number: "04",
    title: "Export Reports",
    description:
      "Download professional PDF reports and AI-generated insights with one click.",
    icon: <FileDown size={42} />,
  },
];

export default function HowItWorks() {
  return (
    <section
      id="how-it-works"
      className="bg-white py-28"
    >
      <div className="mx-auto max-w-7xl px-6">

        <div className="mb-20 text-center">

          <span className="rounded-full bg-indigo-100 px-4 py-2 text-sm font-semibold text-indigo-700">
            Workflow
          </span>

          <h2 className="mt-6 text-4xl font-bold">
            How InsightForge AI Works
          </h2>

          <p className="mt-4 text-slate-600">
            Analyze your data in four simple steps.
          </p>

        </div>

        <div className="grid gap-8 lg:grid-cols-4">

          {steps.map((step, index) => (
            <div key={step.number} className="relative">

              <StepCard {...step} />

              {index < steps.length - 1 && (
                <ArrowRight
                  className="absolute -right-6 top-1/2 hidden text-indigo-400 lg:block"
                  size={28}
                />
              )}

            </div>
          ))}

        </div>

      </div>
    </section>
  );
}