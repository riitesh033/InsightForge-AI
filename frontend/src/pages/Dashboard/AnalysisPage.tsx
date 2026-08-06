import { useParams } from "react-router-dom";

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

  const { datasetId } = useParams<{ datasetId: string }>();

  const {
    data,
    loading,
    error,
  } = useAnalysis(datasetId);


  if (loading) {
    return (
      <div className="p-8">
        Loading analysis...
      </div>
    );
  }


  if (error) {
    return (
      <div className="p-8 text-red-500">
        {error}
      </div>
    );
  }


  if (!data) {
    return (
      <div className="p-8">
        No analysis found.
      </div>
    );
  }


  return (
    <div className="space-y-8">


      {/* Header */}
      <div className="flex items-center justify-between">

        <div>
          <h1 className="text-3xl font-bold">
            Dataset Analysis
          </h1>

          <p className="text-muted-foreground">
            AI powered data quality report
          </p>
        </div>


        <ReportButton
          datasetId={data.dataset_id}
        />

      </div>



      {/* Quality Score */}

      <QualityScore
        score={data.quality_score}
      />



      {/* Statistics */}

      <AnalysisStats
        summary={data.summary}
        missingValues={data.missing_values}
        duplicates={data.duplicates}
      />



      {/* Columns */}

      <ColumnInfoTable
        columnInfo={data.column_info}
        statistics={data.statistics}
      />



      {/* Quality Charts */}

      <div className="grid gap-6 lg:grid-cols-2">

        <MissingValuesChart
          missingValues={data.missing_values}
        />


        <DuplicateCard
          duplicates={data.duplicates}
        />

      </div>



      {/* Correlation */}

      {data.correlations && (
        <CorrelationHeatmap
          correlations={data.correlations}
        />
      )}



      {/* Outliers */}

      {data.outliers && (
        <OutlierCard
          outliers={data.outliers}
        />
      )}



      {/* AI Summary */}

      <AIInsights
        summary={data.summary_text}
      />


    </div>
  );
}