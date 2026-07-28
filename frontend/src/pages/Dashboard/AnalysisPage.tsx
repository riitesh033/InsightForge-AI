import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import SummaryCard from "@/components/dashboard/SummaryCard";
import ColumnTable from "@/components/dashboard/ColumnTable";
import MissingValuesCard from "@/components/dashboard/MissingValuesCard";

import {
  Analysis,
  getAnalysis,
} from "@/services/analysis";

export default function AnalysisPage() {
  const { id } = useParams();

  const [analysis, setAnalysis] =
    useState<Analysis | null>(null);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {
    async function load() {
      if (!id) return;

      const data = await getAnalysis(Number(id));

      setAnalysis(data);

      setLoading(false);
    }

    load();
  }, [id]);

  if (loading) {
    return (
      <div className="text-center">
        Loading...
      </div>
    );
  }

  if (!analysis) {
    return (
      <div>
        Analysis not found.
      </div>
    );
  }

  const summary = analysis.summary;

  return (
    <div className="space-y-8">

      <div>
        <h1 className="text-3xl font-bold">
          Dataset Analysis
        </h1>

        <p className="mt-2 text-muted-foreground">
          Complete overview of your uploaded dataset.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-5">

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

        <ColumnTable
            columns={analysis.column_info}
        />

        <MissingValuesCard
          missingValues={analysis.missing_values}
        />

      </div>

    </div>
  );
}