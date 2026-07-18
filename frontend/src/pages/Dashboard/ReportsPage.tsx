import {
  FileText,
  Download,
  Calendar,
  Sparkles,
  Eye,
} from "lucide-react";

export default function ReportsPage() {
  return (
    <div className="space-y-8">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">
          AI Reports
        </h1>

        <p className="mt-2 text-muted-foreground">
          View, manage and download AI-generated reports for your datasets.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-6 md:grid-cols-3">

        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between">

            <div>
              <p className="text-sm text-muted-foreground">
                Total Reports
              </p>

              <h2 className="mt-2 text-3xl font-bold text-foreground">
                0
              </h2>
            </div>

            <div className="rounded-lg bg-primary/10 p-3">
              <FileText className="text-primary" size={24} />
            </div>

          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between">

            <div>
              <p className="text-sm text-muted-foreground">
                AI Insights
              </p>

              <h2 className="mt-2 text-3xl font-bold text-foreground">
                0
              </h2>
            </div>

            <div className="rounded-lg bg-primary/10 p-3">
              <Sparkles className="text-primary" size={24} />
            </div>

          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between">

            <div>
              <p className="text-sm text-muted-foreground">
                Downloads
              </p>

              <h2 className="mt-2 text-3xl font-bold text-foreground">
                0
              </h2>
            </div>

            <div className="rounded-lg bg-primary/10 p-3">
              <Download className="text-primary" size={24} />
            </div>

          </div>
        </div>

      </div>

      {/* Reports Table */}
      <div className="overflow-hidden rounded-xl border border-border bg-card">

        <table className="w-full">

          <thead className="bg-muted">

            <tr>

              <th className="px-6 py-4 text-left text-sm font-semibold">
                Report Name
              </th>

              <th className="px-6 py-4 text-left text-sm font-semibold">
                Dataset
              </th>

              <th className="px-6 py-4 text-left text-sm font-semibold">
                Generated On
              </th>

              <th className="px-6 py-4 text-right text-sm font-semibold">
                Actions
              </th>

            </tr>

          </thead>

          <tbody>

            <tr>

              <td
                colSpan={4}
                className="py-20 text-center"
              >

                <FileText
                  size={56}
                  className="mx-auto text-muted-foreground"
                />

                <h2 className="mt-5 text-xl font-semibold text-foreground">
                  No Reports Available
                </h2>

                <p className="mt-2 text-muted-foreground">
                  Upload and analyze a dataset to generate your first AI report.
                </p>

              </td>

            </tr>

          </tbody>

        </table>

      </div>

      {/* Upcoming Features */}
      <div className="rounded-xl border border-border bg-card p-6">

        <div className="flex items-center gap-3">

          <Calendar
            className="text-primary"
            size={22}
          />

          <h2 className="text-xl font-semibold text-foreground">
            Upcoming Report Features
          </h2>

        </div>

        <ul className="mt-5 list-disc space-y-3 pl-6 text-muted-foreground">

          <li>PDF Report Export</li>

          <li>Excel Report Export</li>

          <li>Interactive Charts</li>

          <li>AI Executive Summary</li>

          <li>Business Recommendations</li>

          <li>Missing Value Analysis</li>

          <li>Outlier Detection Summary</li>

          <li>Correlation Heatmaps</li>

          <li>One-click Report Sharing</li>

        </ul>

      </div>

      {/* Preview Buttons */}
      <div className="flex gap-4">

        <button className="flex items-center gap-2 rounded-lg border border-border bg-background px-5 py-3 hover:bg-accent">

          <Eye size={18} />

          Preview

        </button>

        <button className="flex items-center gap-2 rounded-lg bg-primary px-5 py-3 text-primary-foreground hover:opacity-90">

          <Download size={18} />

          Download PDF

        </button>

      </div>

    </div>
  );
}