import { useEffect, useState } from "react";

import {
  AnalysisData,
  getAnalysis,
} from "@/services/analysis";


export function useAnalysis(
  datasetId?: string
) {

  const [data, setData] =
    useState<AnalysisData | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  useEffect(() => {

    if (!datasetId)
      return;

    loadAnalysis();

  }, [datasetId]);


  async function loadAnalysis() {

    try {

      setLoading(true);

      const result =
        await getAnalysis(
          Number(datasetId)
        );

      setData(result);

    } catch {

      setError(
        "Failed to load analysis."
      );

    } finally {

      setLoading(false);

    }

  }


  return {
    data,
    loading,
    error,
    reload: loadAnalysis,
  };
}