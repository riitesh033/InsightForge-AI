import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import SummaryCard from "@/components/dashboard/SummaryCard";
import ColumnTable from "@/components/dashboard/ColumnTable";
import MissingValuesCard from "@/components/dashboard/MissingValuesCard";
import StatisticsTable from "@/components/dashboard/StatisticsTable";
import MissingValuesChart from "@/components/dashboard/MissingValuesChart";
import DataTypePieChart from "@/components/dashboard/DataTypePieChart";
import CorrelationTable from "@/components/dashboard/CorrelationTable";
import OutlierTable from "@/components/dashboard/OutlierTable";
import AISummaryCard from "@/components/dashboard/AISummaryCard";
import QualityScoreCard from "@/components/dashboard/QualityScoreCard";

import {
  Analysis,
  getAnalysis,
} from "@/services/analysis";

export default function AnalysisPage() {
  const { datasetId } = useParams();

  const [analysis, setAnalysis] =
    useState<Analysis | null>(null);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {
    async function load() {
      if (!datasetId) return;

      try {
        const data = await getAnalysis(Number(datasetId));
        setAnalysis(data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [datasetId]);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        Loading...
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="flex h-96 items-center justify-center">
        Analysis not found.
      </div>
    );
  }

  const summary = analysis.summary;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">
          Dataset Analysis
        </h1>

        <p className="mt-2 text-muted-foreground">
          Complete overview of your uploaded dataset.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-5">
        <SummaryCard
          title="Rows"
          value={summary.rows}
        />

        <SummaryCard
          title="Columns"
          value={summary.columns}
        />

        <SummaryCard
          title="Memory"
          value={`${(
            summary.memory_usage / 1024
          ).toFixed(2)} KB`}
        />

        <SummaryCard
          title="Missing Cells"
          value={summary.missing_cells}
        />

        <SummaryCard
          title="Duplicate Rows"
          value={summary.duplicate_rows}
        />
      </div>

      {/* AI Summary */}
      <AISummaryCard
        summary={analysis.summary_text}
      />

      <QualityScoreCard
        score={analysis.quality_score}
      />

      {/* Column Information */}
      <ColumnTable
        columns={analysis.column_info}
      />

      {/* Missing Values */}
      <MissingValuesCard
        missingValues={analysis.missing_values}
      />

      {/* Statistics */}
      <StatisticsTable
        statistics={analysis.statistics}
      />

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <MissingValuesChart
          missingValues={analysis.missing_values}
        />

        <DataTypePieChart
          columns={analysis.column_info}
        />
      </div>

      {/* Correlation & Outliers */}
      <div className="grid gap-6 lg:grid-cols-2">
        <CorrelationTable
          correlations={analysis.correlations}
        />

        <OutlierTable
          outliers={analysis.outliers}
        />
      </div>
    </div>
  );
}