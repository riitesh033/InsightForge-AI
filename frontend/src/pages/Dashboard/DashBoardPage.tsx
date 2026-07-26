import { useEffect, useState } from "react";
import {
  Database,
  Upload,
  FileText,
  Brain,
  TrendingUp,
  Activity,
} from "lucide-react";

import { Dataset, getDatasets } from "@/services/dataset";

export default function DashboardPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDatasets();
  }, []);

  async function loadDatasets() {
    try {
      const data = await getDatasets();
      setDatasets(data);
    } catch (error) {
      console.error("Failed to load datasets:", error);
    } finally {
      setLoading(false);
    }
  }

  const stats = [
    {
      title: "Datasets",
      value: datasets.length,
      icon: Database,
    },
    {
      title: "Reports",
      value: 0,
      icon: FileText,
    },
    {
      title: "AI Insights",
      value: 0,
      icon: Brain,
    },
    {
      title: "Uploads",
      value: datasets.length,
      icon: Upload,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">
          Dashboard
        </h1>

        <p className="mt-2 text-muted-foreground">
          Welcome back! Here's an overview of your datasets and AI analysis.
        </p>
      </div>

      {/* Statistics */}
      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((item) => {
          const Icon = item.icon;

          return (
            <div
              key={item.title}
              className="rounded-xl border border-border bg-card p-6 shadow-sm transition hover:shadow-lg"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">
                    {item.title}
                  </p>

                  <h2 className="mt-2 text-3xl font-bold text-foreground">
                    {loading ? "..." : String(item.value)}
                  </h2>
                </div>

                <div className="rounded-lg bg-primary/10 p-3">
                  <Icon
                    size={24}
                    className="text-primary"
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-xl border border-border bg-card p-6 lg:col-span-2">
          <div className="flex items-center gap-2">
            <Activity
              size={20}
              className="text-primary"
            />

            <h2 className="text-xl font-semibold text-foreground">
              Recent Datasets
            </h2>
          </div>

          <div className="mt-6">
            {datasets.length === 0 ? (
              <div className="flex h-56 items-center justify-center rounded-lg border border-dashed border-border">
                <p className="text-muted-foreground">
                  No datasets uploaded yet.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {datasets.slice(0, 5).map((dataset) => (
                  <div
                    key={dataset.id}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div>
                      <h3 className="font-semibold text-foreground">
                        {dataset.original_filename}
                      </h3>

                      <p className="text-sm text-muted-foreground">
                        {dataset.rows} rows • {dataset.columns} columns
                      </p>
                    </div>

                    <span className="text-sm text-muted-foreground">
                      {dataset.file_type.toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center gap-2">
            <TrendingUp
              size={20}
              className="text-primary"
            />

            <h2 className="text-xl font-semibold text-foreground">
              AI Insights
            </h2>
          </div>

          <div className="mt-6 flex h-56 items-center justify-center rounded-lg border border-dashed border-border">
            <p className="text-center text-muted-foreground">
              Upload a dataset to generate AI-powered insights.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}