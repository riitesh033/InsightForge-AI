import { useEffect, useState } from "react";
import {
  FileText,
  Download,
  Eye,
  RefreshCw,
  FileBarChart,
  CheckCircle2,
  XCircle,
} from "lucide-react";

import {
  getReports,
  downloadReport,
  savePdf,
  type Report,
} from "@/services/report";

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloadingId, setDownloadingId] = useState<number | null>(
    null
  );
  const [previewingId, setPreviewingId] = useState<number | null>(
    null
  );

  async function loadReports() {
    try {
      setLoading(true);
      setError("");

      const data = await getReports();

      setReports(data);
    } catch (err) {
      console.error("Failed to load reports:", err);

      setError(
        "Unable to load reports. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReports();
  }, []);

  async function handleDownload(report: Report) {
    try {
      setDownloadingId(report.dataset_id);

      const blob = await downloadReport(report.dataset_id);

      const baseName = report.dataset_name
        .replace(/\.[^/.]+$/, "")
        .replace(/[^a-zA-Z0-9-_ ]/g, "")
        .trim();

      savePdf(
        blob,
        `${baseName || "dataset"}_analysis_report.pdf`
      );
    } catch (err) {
      console.error("Failed to download report:", err);

      setError(
        "Unable to download the report. Please try again."
      );
    } finally {
      setDownloadingId(null);
    }
  }

  async function handlePreview(report: Report) {
    try {
      setPreviewingId(report.dataset_id);

      const blob = await downloadReport(report.dataset_id);

      const url = window.URL.createObjectURL(blob);

      window.open(url, "_blank");

      setTimeout(() => {
        window.URL.revokeObjectURL(url);
      }, 60000);
    } catch (err) {
      console.error("Failed to preview report:", err);

      setError(
        "Unable to preview the report. Please try again."
      );
    } finally {
      setPreviewingId(null);
    }
  }

  const averageQuality =
    reports.length > 0
      ? Math.round(
          reports.reduce(
            (sum, report) => sum + report.quality_score,
            0
          ) / reports.length
        )
      : 0;

  const excellentReports = reports.filter(
    (report) => report.quality_score >= 80
  ).length;

  const needsAttention = reports.filter(
    (report) => report.quality_score < 60
  ).length;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10">
              <FileBarChart className="h-6 w-6 text-primary" />
            </div>

            <div>
              <h1 className="text-2xl font-bold text-foreground">
                Reports
              </h1>

              <p className="text-sm text-muted-foreground">
                View and download your dataset analysis reports.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={loadReports}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-60"
        >
          <RefreshCw
            className={`h-4 w-4 ${
              loading ? "animate-spin" : ""
            }`}
          />

          Refresh
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center justify-between gap-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300">
          <span>{error}</span>

          <button
            onClick={() => setError("")}
            className="font-medium hover:underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Statistics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Reports"
          value={reports.length}
          icon={FileText}
        />

        <StatCard
          title="Average Quality"
          value={`${averageQuality}/100`}
          icon={FileBarChart}
        />

        <StatCard
          title="Good Quality"
          value={excellentReports}
          icon={CheckCircle2}
        />

        <StatCard
          title="Needs Attention"
          value={needsAttention}
          icon={XCircle}
        />
      </div>

      {/* Reports */}
      <div className="rounded-xl border border-border bg-card shadow-sm">
        <div className="border-b border-border px-6 py-5">
          <h2 className="text-lg font-semibold text-foreground">
            Analysis Reports
          </h2>

          <p className="mt-1 text-sm text-muted-foreground">
            Reports are available for datasets that have completed analysis.
          </p>
        </div>

        {loading ? (
          <LoadingState />
        ) : reports.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            {/* Desktop table */}
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border bg-muted/40 text-left text-sm">
                    <th className="px-6 py-4 font-medium">
                      Dataset
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Quality Score
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Uploaded
                    </th>

                    <th className="px-6 py-4 text-right font-medium">
                      Actions
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {reports.map((report) => (
                    <ReportRow
                      key={report.analysis_id}
                      report={report}
                      downloading={
                        downloadingId === report.dataset_id
                      }
                      previewing={
                        previewingId === report.dataset_id
                      }
                      onDownload={() =>
                        handleDownload(report)
                      }
                      onPreview={() =>
                        handlePreview(report)
                      }
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile cards */}
            <div className="divide-y divide-border md:hidden">
              {reports.map((report) => (
                <ReportCard
                  key={report.analysis_id}
                  report={report}
                  downloading={
                    downloadingId === report.dataset_id
                  }
                  previewing={
                    previewingId === report.dataset_id
                  }
                  onDownload={() =>
                    handleDownload(report)
                  }
                  onPreview={() =>
                    handlePreview(report)
                  }
                />
              ))}
            </div>
          </>
        )}
      </div>

      {/* Information */}
      <div className="rounded-xl border border-border bg-muted/30 p-6">
        <h2 className="text-base font-semibold text-foreground">
          About Analysis Reports
        </h2>

        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          Each report contains the dataset quality score, dataset
          summary, missing-value analysis, duplicate records,
          outlier detection, and AI-generated insights.
        </p>
      </div>
    </div>
  );
}


/* ----------------------------------------
   Components
----------------------------------------- */

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
}

function StatCard({
  title,
  value,
  icon: Icon,
}: StatCardProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {title}
        </p>

        <Icon className="h-5 w-5 text-muted-foreground" />
      </div>

      <p className="mt-3 text-2xl font-bold text-foreground">
        {value}
      </p>
    </div>
  );
}


function LoadingState() {
  return (
    <div className="space-y-4 p-6">
      {[1, 2, 3].map((item) => (
        <div
          key={item}
          className="h-16 animate-pulse rounded-lg bg-muted"
        />
      ))}
    </div>
  );
}


function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
        <FileText className="h-8 w-8 text-muted-foreground" />
      </div>

      <h3 className="mt-5 text-lg font-semibold text-foreground">
        No reports available
      </h3>

      <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
        Upload a dataset and complete its analysis. Your
        generated analysis report will appear here.
      </p>
    </div>
  );
}


/* ----------------------------------------
   Desktop row
----------------------------------------- */

interface ReportItemProps {
  report: Report;
  downloading: boolean;
  previewing: boolean;
  onDownload: () => void;
  onPreview: () => void;
}

function ReportRow({
  report,
  downloading,
  previewing,
  onDownload,
  onPreview,
}: ReportItemProps) {
  return (
    <tr className="border-b border-border last:border-0">
      <td className="px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <FileText className="h-5 w-5 text-primary" />
          </div>

          <div className="min-w-0">
            <p className="truncate font-medium text-foreground">
              {report.dataset_name}
            </p>

            <p className="text-xs text-muted-foreground">
              Analysis #{report.analysis_id}
            </p>
          </div>
        </div>
      </td>

      <td className="px-6 py-5">
        <QualityBadge score={report.quality_score} />
      </td>

      <td className="px-6 py-5 text-sm text-muted-foreground">
        {formatDate(report.uploaded_at)}
      </td>

      <td className="px-6 py-5">
        <div className="flex justify-end gap-2">
          <ActionButton
            icon={Eye}
            label="Preview"
            loading={previewing}
            onClick={onPreview}
          />

          <ActionButton
            icon={Download}
            label="Download"
            loading={downloading}
            onClick={onDownload}
          />
        </div>
      </td>
    </tr>
  );
}


/* ----------------------------------------
   Mobile card
----------------------------------------- */

function ReportCard({
  report,
  downloading,
  previewing,
  onDownload,
  onPreview,
}: ReportItemProps) {
  return (
    <div className="space-y-4 p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
          <FileText className="h-5 w-5 text-primary" />
        </div>

        <div className="min-w-0 flex-1">
          <p className="break-words font-medium text-foreground">
            {report.dataset_name}
          </p>

          <p className="mt-1 text-xs text-muted-foreground">
            Analysis #{report.analysis_id}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-muted-foreground">
            Quality
          </p>

          <div className="mt-1">
            <QualityBadge score={report.quality_score} />
          </div>
        </div>

        <div className="text-right">
          <p className="text-xs text-muted-foreground">
            Uploaded
          </p>

          <p className="mt-1 text-sm text-foreground">
            {formatDate(report.uploaded_at)}
          </p>
        </div>
      </div>

      <div className="flex gap-2">
        <ActionButton
          icon={Eye}
          label="Preview"
          loading={previewing}
          onClick={onPreview}
          fullWidth
        />

        <ActionButton
          icon={Download}
          label="Download"
          loading={downloading}
          onClick={onDownload}
          fullWidth
        />
      </div>
    </div>
  );
}


/* ----------------------------------------
   Quality badge
----------------------------------------- */

function QualityBadge({
  score,
}: {
  score: number;
}) {
  let className = "";

  if (score >= 80) {
    className =
      "bg-green-100 text-green-700 dark:bg-green-950/40 dark:text-green-300";
  } else if (score >= 60) {
    className =
      "bg-yellow-100 text-yellow-700 dark:bg-yellow-950/40 dark:text-yellow-300";
  } else {
    className =
      "bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-300";
  }

  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${className}`}
    >
      {score}/100
    </span>
  );
}


/* ----------------------------------------
   Action button
----------------------------------------- */

interface ActionButtonProps {
  icon: React.ElementType;
  label: string;
  loading: boolean;
  onClick: () => void;
  fullWidth?: boolean;
}

function ActionButton({
  icon: Icon,
  label,
  loading,
  onClick,
  fullWidth = false,
}: ActionButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium text-foreground transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-60 ${
        fullWidth ? "flex-1" : ""
      }`}
    >
      {loading ? (
        <RefreshCw className="h-4 w-4 animate-spin" />
      ) : (
        <Icon className="h-4 w-4" />
      )}

      {loading ? "Please wait..." : label}
    </button>
  );
}


/* ----------------------------------------
   Helpers
----------------------------------------- */

function formatDate(date: string) {
  return new Date(date).toLocaleDateString(
    undefined,
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    }
  );
}