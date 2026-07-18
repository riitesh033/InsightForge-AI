import {
  Database,
  Upload,
  FileText,
  Brain,
  TrendingUp,
  Activity,
} from "lucide-react";

const stats = [
  {
    title: "Datasets",
    value: "0",
    icon: Database,
  },
  {
    title: "Reports",
    value: "0",
    icon: FileText,
  },
  {
    title: "AI Insights",
    value: "0",
    icon: Brain,
  },
  {
    title: "Uploads",
    value: "0",
    icon: Upload,
  },
];

export default function DashboardPage() {
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

      {/* Statistics Cards */}
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
                    {item.value}
                  </h2>

                </div>

                <div className="rounded-lg bg-primary/10 p-3">
                  <Icon
                    className="text-primary"
                    size={24}
                  />
                </div>

              </div>
            </div>
          );
        })}

      </div>

      {/* Main Grid */}
      <div className="grid gap-6 lg:grid-cols-3">

        {/* Dataset Activity */}
        <div className="rounded-xl border border-border bg-card p-6 lg:col-span-2">

          <div className="flex items-center gap-2">

            <Activity
              className="text-primary"
              size={20}
            />

            <h2 className="text-xl font-semibold text-foreground">
              Recent Dataset Activity
            </h2>

          </div>

          <div className="mt-8 flex h-64 items-center justify-center rounded-lg border border-dashed border-border">

            <p className="text-muted-foreground">
              No datasets uploaded yet.
            </p>

          </div>

        </div>

        {/* AI Insights */}
        <div className="rounded-xl border border-border bg-card p-6">

          <div className="flex items-center gap-2">

            <TrendingUp
              className="text-primary"
              size={20}
            />

            <h2 className="text-xl font-semibold text-foreground">
              AI Insights
            </h2>

          </div>

          <div className="mt-8 flex h-64 items-center justify-center rounded-lg border border-dashed border-border">

            <p className="text-center text-muted-foreground">
              Upload a dataset to generate AI-powered insights.
            </p>

          </div>

        </div>

      </div>

    </div>
  );
}