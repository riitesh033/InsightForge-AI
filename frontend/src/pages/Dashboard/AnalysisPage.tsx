import { useEffect, useState } from "react";
import {
  ArrowLeft,
  MessageSquare,
} from "lucide-react";
import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  Dataset,
  getDatasets,
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