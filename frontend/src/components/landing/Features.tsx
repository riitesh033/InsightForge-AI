import FeatureCard from "./FeatureCard";

import {
  Upload,
  Brain,
  BarChart3,
  FileText,
  Search,
  Sparkles,
} from "lucide-react";

import Container from "@/components/ui/Container";

export default function Features() {
  const features = [
    {
      title: "Upload Datasets",
      description: "Upload CSV and Excel files instantly.",
      icon: <Upload className="h-8 w-8" />,
    },
    {
      title: "AI Analysis",
      description:
        "Automatically detect missing values, duplicates, and outliers.",
      icon: <Brain className="h-8 w-8" />,
    },
    {
      title: "Interactive Dashboards",
      description:
        "Generate charts and analytics dashboards instantly.",
      icon: <BarChart3 className="h-8 w-8" />,
    },
    {
      title: "AI Reports",
      description:
        "Create downloadable PDF reports with AI insights.",
      icon: <FileText className="h-8 w-8" />,
    },
    {
      title: "Dataset Profiling",
      description:
        "Understand your dataset quality in seconds.",
      icon: <Search className="h-8 w-8" />,
    },
    {
      title: "Smart Recommendations",
      description:
        "Receive AI-powered suggestions to improve your data.",
      icon: <Sparkles className="h-8 w-8" />,
    },
  ];

  return (
    <section
      id="features"
      className="bg-transparent py-28"
    >
      <Container>

        <div className="mx-auto mb-16 max-w-3xl text-center">

          <h2 className="text-4xl font-bold text-foreground lg:text-5xl">
            Powerful Features
          </h2>

          <p className="mt-6 text-lg text-muted-foreground">
            Everything you need to upload, analyze, visualize,
            clean, and understand your datasets using AI.
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

      </Container>
    </section>
  );
}