import FeatureCard from "./FeatureCard";

import {
  Upload,
  Brain,
  BarChart3,
  FileText,
  Search,
  Sparkles,
} from "lucide-react";

export default function Features() {
  const features = [
    {
      title: "Upload Datasets",
      description:
        "Upload CSV and Excel files instantly.",
      icon: <Upload size={32} />,
    },

    {
      title: "AI Analysis",
      description:
        "Automatically detect missing values, duplicates and outliers.",
      icon: <Brain size={32} />,
    },

    {
      title: "Interactive Dashboards",
      description:
        "Generate charts and analytics dashboards instantly.",
      icon: <BarChart3 size={32} />,
    },

    {
      title: "AI Reports",
      description:
        "Create downloadable PDF reports with insights.",
      icon: <FileText size={32} />,
    },

    {
      title: "Dataset Profiling",
      description:
        "Understand dataset quality in seconds.",
      icon: <Search size={32} />,
    },

    {
      title: "Smart Recommendations",
      description:
        "Get AI-powered suggestions to improve your data.",
      icon: <Sparkles size={32} />,
    },
  ];

  return (
    <section id="features" className="bg-slate-50 dark:bg-slate-900">
    
      <div className="mx-auto max-w-7xl px-6">

        <div className="mb-16 text-center">

          <h2 className="text-4xl font-bold">
             Features
          </h2>

          <p className="mt-4 text-slate-600">
            Everything you need for modern AI-powered
            data analysis.
          </p>

        </div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">

          {features.map((feature) => (
            <FeatureCard
              key={feature.title}
              title={feature.title}
              description={feature.description}
              icon={feature.icon}
            />
          ))}

        </div>

      </div>
    </section>
  );
}