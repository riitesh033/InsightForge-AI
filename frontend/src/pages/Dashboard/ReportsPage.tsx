import { useEffect, useState } from "react";
import {
  FileText,
  Download,
  Calendar,
  Sparkles,
  Eye,
} from "lucide-react";

import {
  Dataset,
  getDatasets,
} from "@/services/dataset";

import api from "@/lib/api";

interface ReportItem extends Dataset {
  reportAvailable: boolean;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<number | null>(
    null
  );
  const [error, setError] = useState("");

  useEffect(() => {
    loadReports();
  }, []);

  // =========================
  // Load Reports
  // =========================

  async function loadReports() {
    try {
      setLoading(true);
      setError("");

      const response = await getDatasets();

      const items: ReportItem[] = response.items.map(
        (dataset) => ({
          ...dataset,
          reportAvailable: true,
        })
      );

      setReports(items);
    } catch (err) {
      console.error(
        "Reports loading error:",
        err
      );

      setError(
        "Failed to load reports."
      );
    } finally {
      setLoading(false);
    }
  }

  // =========================
  // Download PDF
  // =========================

  async function downloadReport(
    datasetId: number,
    filename: string
  ) {
    try {
      setDownloadingId(datasetId);
      setError("");

      const response = await api.get(
        `/reports/${datasetId}/download`,
        {
          responseType: "blob",
        }
      );

      const blob = new Blob(
        [response.data],
        {
          type: "application/pdf",
        }
      );

      const url =
        window.URL.createObjectURL(blob);

      const link =
        document.createElement("a");

      link.href = url;

      link.download =
        `${filename.replace(/\.[^/.]+$/, "")}_analysis_report.pdf`;

      document.body.appendChild(link);

      link.click();

      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(
        "Report download error:",
        err
      );

      setError(
        "Failed to download the report."
      );
    } finally {
      setDownloadingId(null);
    }
  }

  // =========================
  // Preview
  // =========================

  async function previewReport(
    datasetId: number
  ) {
    try {
      setError("");

      const response = await api.get(
        `/reports/${datasetId}/download`,
        {
          responseType: "blob",
        }
      );

      const blob = new Blob(
        [response.data],
        {
          type: "application/pdf",
        }
      );

      const url =
        window.URL.createObjectURL(blob);

      window.open(
        url,
        "_blank",
        "noopener,noreferrer"
      );

      setTimeout(() => {
        window.URL.revokeObjectURL(url);
      }, 60000);
    } catch (err) {
      console.error(
        "Report preview error:",
        err
      );

      setError(
        "Failed to preview the report."
      );
    }
  }

  // =========================
  // Loading
  // =========================

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <FileText
            size={48}
            className="mx-auto text-muted-foreground"
          />

          <p className="mt-4 text-muted-foreground">
            Loading reports...
          </p>
        </div>
      </div>
    );
  }

  // =========================
  // Page
  // =========================

  return (
    <div className="space-y-8">

      {/* Header */}

      <div>
        <h1 className="text-3xl font-bold text-foreground">
          AI Reports
        </h1>

        <p className="mt-2 text-muted-foreground">
          View, manage and download AI-generated
          reports for your datasets.
        </p>
      </div>


      {/* Error */}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
          {error}
        </div>
      )}


      {/* Summary Cards */}

      <div className="grid gap-6 md:grid-cols-3">

        {/* Total Reports */}

        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">

          <div className="flex items-center justify-between">

            <div>

              <p className="text-sm text-muted-foreground">
                Total Reports
              </p>

              <h2 className="mt-2 text-3xl font-bold text-foreground">
                {reports.length}
              </h2>

            </div>

            <div className="rounded-lg bg-primary/10 p-3">
              <FileText
                className="text-primary"
                size={24}
              />
            </div>

          </div>

        </div>


        {/* AI Insights */}

        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">

          <div className="flex items-center justify-between">

            <div>

              <p className="text-sm text-muted-foreground">
                AI Insights
              </p>

              <h2 className="mt-2 text-3xl font-bold text-foreground">
                {reports.length}
              </h2>

            </div>

            <div className="rounded-lg bg-primary/10 p-3">
              <Sparkles
                className="text-primary"
                size={24}
              />
            </div>

          </div>

        </div>


        {/* Downloads */}

        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">

          <div className="flex items-center justify-between">

            <div>

              <p className="text-sm text-muted-foreground">
                Reports Ready
              </p>

              <h2 className="mt-2 text-3xl font-bold text-foreground">
                {reports.length}
              </h2>

            </div>

            <div className="rounded-lg bg-primary/10 p-3">
              <Download
                className="text-primary"
                size={24}
              />
            </div>

          </div>

        </div>

      </div>


      {/* Reports */}

      <div className="overflow-hidden rounded-xl border border-border bg-card">

        {reports.length === 0 ? (

          <div className="py-20 text-center">

            <FileText
              size={56}
              className="mx-auto text-muted-foreground"
            />

            <h2 className="mt-5 text-xl font-semibold text-foreground">
              No Reports Available
            </h2>

            <p className="mt-2 text-muted-foreground">
              Upload and analyze a dataset to
              generate your first AI report.
            </p>

          </div>

        ) : (

          <div className="overflow-x-auto">

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

                {reports.map((report) => (

                  <tr
                    key={report.id}
                    className="border-t border-border transition hover:bg-muted/50"
                  >

                    {/* Report Name */}

                    <td className="px-6 py-5">

                      <div className="flex items-center gap-3">

                        <div className="rounded-lg bg-primary/10 p-2">

                          <FileText
                            size={20}
                            className="text-primary"
                          />

                        </div>

                        <div>

                          <p className="font-medium text-foreground">
                            Dataset Analysis Report
                          </p>

                          <p className="text-xs text-muted-foreground">
                            Analysis #{report.id}
                          </p>

                        </div>

                      </div>

                    </td>


                    {/* Dataset */}

                    <td className="px-6 py-5">

                      <p className="font-medium text-foreground">
                        {report.original_filename}
                      </p>

                      <p className="text-sm text-muted-foreground">
                        {report.rows} rows × {report.columns} columns
                      </p>

                    </td>


                    {/* Date */}

                    <td className="px-6 py-5">

                      <div className="flex items-center gap-2 text-sm text-muted-foreground">

                        <Calendar size={16} />

                        {new Date(
                          report.uploaded_at
                        ).toLocaleDateString()}

                      </div>

                    </td>


                    {/* Actions */}

                    <td className="px-6 py-5">

                      <div className="flex justify-end gap-2">

                        {/* Preview */}

                        <button
                          onClick={() =>
                            previewReport(
                              report.id
                            )
                          }
                          className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm transition hover:bg-accent"
                        >

                          <Eye size={16} />

                          Preview

                        </button>


                        {/* Download */}

                        <button
                          onClick={() =>
                            downloadReport(
                              report.id,
                              report.original_filename
                            )
                          }
                          disabled={
                            downloadingId ===
                            report.id
                          }
                          className="inline-flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                        >

                          <Download size={16} />

                          {downloadingId ===
                          report.id
                            ? "Downloading..."
                            : "Download"}

                        </button>

                      </div>

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </div>


      {/* Information */}

      <div className="rounded-xl border border-border bg-card p-6">

        <div className="flex items-center gap-3">

          <Sparkles
            className="text-primary"
            size={22}
          />

          <h2 className="text-xl font-semibold text-foreground">
            What's Included
          </h2>

        </div>

        <div className="mt-5 grid gap-3 text-muted-foreground sm:grid-cols-2">

          <p>✓ Dataset summary</p>

          <p>✓ Data quality score</p>

          <p>✓ Missing value analysis</p>

          <p>✓ Duplicate detection</p>

          <p>✓ Outlier detection</p>

          <p>✓ AI-generated insights</p>

        </div>

      </div>

    </div>
  );
}