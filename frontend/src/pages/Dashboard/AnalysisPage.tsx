import { useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Download,
  Loader2,
  MessageSquare,
  Sparkles,
} from "lucide-react";
import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  Dataset,
  getDatasets,
  previewCleaning,
  applyCleaning,
  downloadCleanedDataset,
  CleaningResponse,
} from "@/services/dataset";

import { useAnalysis } from "@/hooks/useAnalysis";

import AnalysisStats from "@/components/analysis/AnalysisStats";
import QualityScore from "@/components/analysis/QualityScore";
import ColumnInfoTable from "@/components/analysis/ColumnInfoTable";
import MissingValuesChart from "@/components/analysis/MissingValuesChart";
import DuplicateCard from "@/components/analysis/DuplicateCard";
import CorrelationHeatmap from "@/components/analysis/CorrelationHeatmap";
import OutlierCard from "@/components/analysis/OutlierCard";
import AIInsights from "@/components/analysis/AIInsights";
import ReportButton from "@/components/analysis/ReportButton";


export default function AnalysisPage() {
  const { datasetId } =
    useParams<{ datasetId: string }>();

  const navigate = useNavigate();

  const {
    data,
    loading,
    error,
  } = useAnalysis(datasetId);


  // ==========================================================
  // Dataset
  // ==========================================================

  const [dataset, setDataset] =
    useState<Dataset | null>(null);

  const [loadingDataset, setLoadingDataset] =
    useState(true);


  // ==========================================================
  // Cleaning State
  // ==========================================================

  const [cleaningData, setCleaningData] =
    useState<CleaningResponse | null>(null);

  const [cleaningLoading, setCleaningLoading] =
    useState(false);

  const [cleaningApplying, setCleaningApplying] =
    useState(false);

  const [cleaningDownloading, setCleaningDownloading] =
    useState(false);

  const [cleaningError, setCleaningError] =
    useState<string | null>(null);

  const [cleaningApplied, setCleaningApplied] =
    useState(false);


  // ==========================================================
  // Load Dataset Information
  // ==========================================================

  useEffect(() => {
    if (!datasetId) {
      setLoadingDataset(false);
      return;
    }

    async function loadDataset() {
      try {
        setLoadingDataset(true);

        const response =
          await getDatasets();

        const foundDataset =
          response.items.find(
            (item) =>
              item.id === Number(datasetId)
          );

        setDataset(
          foundDataset ?? null
        );
      } catch (error) {
        console.error(
          "Failed to load dataset information:",
          error
        );

        setDataset(null);
      } finally {
        setLoadingDataset(false);
      }
    }

    loadDataset();
  }, [datasetId]);


  // ==========================================================
  // Preview Cleaning
  // ==========================================================

  async function handlePreviewCleaning() {
    if (!datasetId) {
      return;
    }

    try {
      setCleaningLoading(true);
      setCleaningError(null);
      setCleaningApplied(false);

      const response =
        await previewCleaning(
          Number(datasetId)
        );

      setCleaningData(response);

    } catch (error: any) {
      console.error(
        "Failed to preview cleaning:",
        error
      );

      setCleaningError(
        error?.response?.data?.detail ??
        "Unable to generate cleaning preview."
      );

    } finally {
      setCleaningLoading(false);
    }
  }


  // ==========================================================
  // Apply Cleaning
  // ==========================================================

  async function handleApplyCleaning() {
    if (!datasetId) {
      return;
    }

    try {
      setCleaningApplying(true);
      setCleaningError(null);

      const response =
        await applyCleaning(
          Number(datasetId)
        );

      setCleaningData(response);
      setCleaningApplied(true);

    } catch (error: any) {
      console.error(
        "Failed to apply cleaning:",
        error
      );

      setCleaningError(
        error?.response?.data?.detail ??
        "Unable to clean the dataset."
      );

    } finally {
      setCleaningApplying(false);
    }
  }


  // ==========================================================
  // Download Cleaned Dataset
  // ==========================================================

  async function handleDownloadCleanedDataset() {
    if (!datasetId) {
      return;
    }

    try {
      setCleaningDownloading(true);
      setCleaningError(null);

      await downloadCleanedDataset(
        Number(datasetId)
      );

    } catch (error: any) {
      console.error(
        "Failed to download cleaned dataset:",
        error
      );

      setCleaningError(
        error?.response?.data?.detail ??
        "Unable to download cleaned dataset."
      );

    } finally {
      setCleaningDownloading(false);
    }
  }


  // ==========================================================
  // Loading
  // ==========================================================

  if (loading || loadingDataset) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />

          <p className="text-muted-foreground">
            Loading analysis...
          </p>
        </div>
      </div>
    );
  }


  // ==========================================================
  // Error
  // ==========================================================

  if (error) {
    return (
      <div className="space-y-4">

        <button
          onClick={() =>
            navigate("/dashboard/datasets")
          }
          className="
            inline-flex
            items-center
            gap-2
            text-sm
            font-medium
            text-muted-foreground
            transition
            hover:text-foreground
          "
        >
          <ArrowLeft size={16} />

          Back to Datasets
        </button>


        <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-red-600 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
          {error}
        </div>

      </div>
    );
  }


  // ==========================================================
  // No Analysis
  // ==========================================================

  if (!data) {
    return (
      <div className="space-y-4">

        <button
          onClick={() =>
            navigate("/dashboard/datasets")
          }
          className="
            inline-flex
            items-center
            gap-2
            text-sm
            font-medium
            text-muted-foreground
            transition
            hover:text-foreground
          "
        >
          <ArrowLeft size={16} />

          Back to Datasets
        </button>


        <div className="rounded-xl border p-8 text-center">
          <h2 className="text-lg font-semibold">
            No analysis found
          </h2>

          <p className="mt-2 text-sm text-muted-foreground">
            This dataset does not have an analysis available yet.
          </p>
        </div>

      </div>
    );
  }


  // ==========================================================
  // Dataset Name
  // ==========================================================

  const datasetName =
    dataset?.original_filename ??
    `Dataset #${data.dataset_id}`;


  // ==========================================================
  // Cleaning Statistics
  // ==========================================================

  const cleaningPreview =
    cleaningData?.preview;

  const totalOutliers =
    cleaningPreview
      ? Object.values(
          cleaningPreview.outliers_detected
        ).reduce(
          (total, count) =>
            total + count,
          0
        )
      : 0;


  // ==========================================================
  // Main
  // ==========================================================

  return (
    <div className="space-y-8">

      {/* =====================================================
          Header
      ====================================================== */}

      <div className="space-y-5">

        {/* Back Button */}

        <button
          onClick={() =>
            navigate("/dashboard/datasets")
          }
          className="
            inline-flex
            items-center
            gap-2
            text-sm
            font-medium
            text-muted-foreground
            transition
            hover:text-foreground
          "
        >
          <ArrowLeft size={16} />

          Back to Datasets
        </button>


        {/* Header Content */}

        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">

          <div className="min-w-0">

            <p className="mb-2 text-sm font-medium text-primary">
              Dataset Analysis
            </p>

            <h1 className="truncate text-3xl font-bold tracking-tight">
              {datasetName}
            </h1>

            <p className="mt-2 text-muted-foreground">
              AI-powered data quality report and analysis
            </p>

          </div>


          {/* Actions */}

          <div className="flex shrink-0 flex-wrap items-center gap-3">

            {/* AI Chat */}

            <button
              onClick={() =>
                navigate(
                  `/dashboard/ai-chat/${data.dataset_id}`
                )
              }
              className="
                inline-flex
                items-center
                gap-2
                rounded-lg
                border
                border-border
                bg-card
                px-4
                py-2.5
                text-sm
                font-medium
                text-foreground
                shadow-sm
                transition
                hover:bg-accent
              "
            >
              <MessageSquare size={17} />

              AI Chat
            </button>


            {/* Report */}

            <ReportButton
              datasetId={data.dataset_id}
            />

          </div>

        </div>

      </div>


      {/* =====================================================
          Quality Score
      ====================================================== */}

      <QualityScore
        score={data.quality_score}
      />


      {/* =====================================================
          Data Cleaning
      ====================================================== */}

      <section
        className="
          overflow-hidden
          rounded-2xl
          border
          border-border
          bg-card
          shadow-sm
        "
      >

        {/* Cleaning Header */}

        <div
          className="
            flex
            flex-col
            gap-4
            border-b
            border-border
            p-6
            sm:flex-row
            sm:items-center
            sm:justify-between
          "
        >

          <div className="flex items-start gap-3">

            <div
              className="
                flex
                h-10
                w-10
                shrink-0
                items-center
                justify-center
                rounded-lg
                bg-primary/10
                text-primary
              "
            >
              <Sparkles size={20} />
            </div>

            <div>

              <h2 className="text-lg font-semibold">
                Data Cleaning
              </h2>

              <p className="mt-1 text-sm text-muted-foreground">
                Automatically fix safe data-quality issues
                without changing the original dataset.
              </p>

            </div>

          </div>


          {!cleaningData && (
            <button
              onClick={handlePreviewCleaning}
              disabled={cleaningLoading}
              className="
                inline-flex
                shrink-0
                items-center
                justify-center
                gap-2
                rounded-lg
                bg-primary
                px-4
                py-2.5
                text-sm
                font-medium
                text-primary-foreground
                transition
                hover:opacity-90
                disabled:cursor-not-allowed
                disabled:opacity-60
              "
            >

              {cleaningLoading ? (
                <>
                  <Loader2
                    size={17}
                    className="animate-spin"
                  />

                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles size={17} />

                  Preview Cleaning
                </>
              )}

            </button>
          )}

        </div>


        {/* Cleaning Error */}

        {cleaningError && (
          <div
            className="
              mx-6
              mt-6
              rounded-lg
              border
              border-red-200
              bg-red-50
              p-4
              text-sm
              text-red-600
              dark:border-red-900
              dark:bg-red-950
              dark:text-red-400
            "
          >
            {cleaningError}
          </div>
        )}


        {/* Cleaning Preview */}

        {cleaningPreview && (
          <div className="space-y-6 p-6">

            {/* Summary */}

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

              <div className="rounded-xl border border-border bg-background p-4">

                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Rows
                </p>

                <div className="mt-2 flex items-end gap-2">

                  <span className="text-2xl font-bold">
                    {cleaningPreview.rows_after.toLocaleString()}
                  </span>

                  {cleaningPreview.rows_before !==
                    cleaningPreview.rows_after && (
                    <span className="mb-1 text-xs text-muted-foreground">
                      from{" "}
                      {cleaningPreview.rows_before.toLocaleString()}
                    </span>
                  )}

                </div>

              </div>


              <div className="rounded-xl border border-border bg-background p-4">

                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Missing Values
                </p>

                <div className="mt-2">

                  <span className="text-2xl font-bold">
                    {cleaningPreview.missing_values_after}
                  </span>

                  <p className="mt-1 text-xs text-muted-foreground">
                    {cleaningPreview.missing_values_filled} fixed
                  </p>

                </div>

              </div>


              <div className="rounded-xl border border-border bg-background p-4">

                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Duplicates
                </p>

                <div className="mt-2">

                  <span className="text-2xl font-bold">
                    {cleaningPreview.duplicates_removed}
                  </span>

                  <p className="mt-1 text-xs text-muted-foreground">
                    rows removed
                  </p>

                </div>

              </div>


              <div className="rounded-xl border border-border bg-background p-4">

                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Outliers
                </p>

                <div className="mt-2">

                  <span className="text-2xl font-bold">
                    {totalOutliers}
                  </span>

                  <p className="mt-1 text-xs text-muted-foreground">
                    detected, not removed
                  </p>

                </div>

              </div>

            </div>


            {/* Changes */}

            {cleaningPreview.changes.length > 0 ? (
              <div>

                <div className="mb-3 flex items-center gap-2">

                  <CheckCircle2
                    size={18}
                    className="text-primary"
                  />

                  <h3 className="font-semibold">
                    Proposed Changes
                  </h3>

                </div>


                <div className="space-y-2">

                  {cleaningPreview.changes.map(
                    (change, index) => (
                      <div
                        key={`${change.action}-${change.column}-${index}`}
                        className="
                          flex
                          flex-col
                          gap-2
                          rounded-lg
                          border
                          border-border
                          bg-background
                          p-4
                          sm:flex-row
                          sm:items-center
                          sm:justify-between
                        "
                      >

                        <div>

                          <p className="text-sm font-medium">

                            {change.column
                              ? change.column
                              : "Dataset"}

                          </p>

                          <p className="mt-1 text-xs text-muted-foreground">
                            {change.action
                              .replace(/_/g, " ")
                              .replace(
                                /^./,
                                (char: string) =>
                                  char.toUpperCase()
                              )}
                          </p>

                        </div>


                        <div className="text-sm font-semibold">

                          {change.count}

                          <span className="ml-1 font-normal text-muted-foreground">
                            affected
                          </span>

                        </div>

                      </div>
                    )
                  )}

                </div>

              </div>
            ) : (
              <div
                className="
                  flex
                  items-start
                  gap-3
                  rounded-xl
                  border
                  border-border
                  bg-background
                  p-4
                "
              >

                <CheckCircle2
                  size={20}
                  className="mt-0.5 shrink-0 text-primary"
                />

                <div>

                  <p className="font-medium">
                    No automatic cleaning required
                  </p>

                  <p className="mt-1 text-sm text-muted-foreground">
                    Your dataset does not contain any
                    issues that InsightForge can safely
                    fix automatically.
                  </p>

                </div>

              </div>
            )}


            {/* Warnings */}

            {cleaningPreview.warnings.length > 0 && (
              <div
                className="
                  rounded-xl
                  border
                  border-yellow-200
                  bg-yellow-50
                  p-4
                  dark:border-yellow-900
                  dark:bg-yellow-950/40
                "
              >

                <div className="flex items-start gap-3">

                  <AlertTriangle
                    size={19}
                    className="mt-0.5 shrink-0 text-yellow-600 dark:text-yellow-400"
                  />

                  <div>

                    <p className="font-medium text-yellow-800 dark:text-yellow-300">
                      Cleaning warnings
                    </p>

                    <ul className="mt-2 space-y-1">

                      {cleaningPreview.warnings.map(
                        (warning, index) => (
                          <li
                            key={index}
                            className="text-sm text-yellow-700 dark:text-yellow-400"
                          >
                            {warning}
                          </li>
                        )
                      )}

                    </ul>

                  </div>

                </div>

              </div>
            )}


            {/* Actions */}

            <div
              className="
                flex
                flex-col
                gap-3
                border-t
                border-border
                pt-6
                sm:flex-row
                sm:items-center
                sm:justify-between
              "
            >

              <div>

                {cleaningApplied ? (
                  <div className="flex items-center gap-2 text-sm font-medium text-primary">

                    <CheckCircle2 size={17} />

                    Cleaned dataset created successfully

                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    The original dataset will not be modified.
                  </p>
                )}

              </div>


              <div className="flex flex-wrap gap-3">

                {!cleaningApplied && (
                  <button
                    onClick={handleApplyCleaning}
                    disabled={cleaningApplying}
                    className="
                      inline-flex
                      items-center
                      justify-center
                      gap-2
                      rounded-lg
                      bg-primary
                      px-4
                      py-2.5
                      text-sm
                      font-medium
                      text-primary-foreground
                      transition
                      hover:opacity-90
                      disabled:cursor-not-allowed
                      disabled:opacity-60
                    "
                  >

                    {cleaningApplying ? (
                      <>
                        <Loader2
                          size={17}
                          className="animate-spin"
                        />

                        Cleaning...
                      </>
                    ) : (
                      <>
                        <Sparkles size={17} />

                        Apply Cleaning
                      </>
                    )}

                  </button>
                )}


                {cleaningApplied && (
                  <button
                    onClick={
                      handleDownloadCleanedDataset
                    }
                    disabled={cleaningDownloading}
                    className="
                      inline-flex
                      items-center
                      justify-center
                      gap-2
                      rounded-lg
                      border
                      border-border
                      bg-background
                      px-4
                      py-2.5
                      text-sm
                      font-medium
                      text-foreground
                      transition
                      hover:bg-accent
                      disabled:cursor-not-allowed
                      disabled:opacity-60
                    "
                  >

                    {cleaningDownloading ? (
                      <>
                        <Loader2
                          size={17}
                          className="animate-spin"
                        />

                        Downloading...
                      </>
                    ) : (
                      <>
                        <Download size={17} />

                        Download Cleaned Dataset
                      </>
                    )}

                  </button>
                )}

              </div>

            </div>

          </div>
        )}

      </section>


      {/* =====================================================
          Statistics
      ====================================================== */}

      <AnalysisStats
        summary={data.summary}
        missingValues={data.missing_values}
        duplicates={data.duplicates}
      />


      {/* =====================================================
          Columns
      ====================================================== */}

      <ColumnInfoTable
        columnInfo={data.column_info}
        statistics={data.statistics}
      />


      {/* =====================================================
          Quality Charts
      ====================================================== */}

      <div className="grid gap-6 lg:grid-cols-2">

        <MissingValuesChart
          missingValues={
            data.missing_values
          }
        />

        <DuplicateCard
          duplicates={
            data.duplicates
          }
        />

      </div>


      {/* =====================================================
          Correlation
      ====================================================== */}

      {data.correlations && (
        <CorrelationHeatmap
          correlations={
            data.correlations
          }
        />
      )}


      {/* =====================================================
          Outliers
      ====================================================== */}

      {data.outliers && (
        <OutlierCard
          outliers={
            data.outliers
          }
        />
      )}


      {/* =====================================================
          AI Summary
      ====================================================== */}

      <AIInsights
        summary={data.summary_text}
      />

    </div>
  );
}