import { useCallback, useEffect, useState } from "react";

import {
  AnalysisData,
  getAnalysis,
} from "@/services/analysis";
import { getApiErrorMessage } from "@/lib/api";


export function useAnalysis(
  datasetId?: string
) {

  const [data, setData] =
    useState<AnalysisData | null>(null);

  const [loading, setLoading] =
    useState<boolean>(true);

  const [error, setError] =
    useState<string>("");



  const loadAnalysis = useCallback(
    async () => {

      if (!datasetId) {

        setError(
          "Dataset ID is missing."
        );

        setLoading(false);

        return;
      }

      const numericDatasetId = Number(datasetId);
      if (!Number.isSafeInteger(numericDatasetId) || numericDatasetId < 1) {
        setError("Invalid dataset ID.");
        setLoading(false);
        return;
      }

      try {

        setLoading(true);
        setError("");

        const response =
          await getAnalysis(
            numericDatasetId
          );

        setData(response);

      } catch (error) {
        setData(null);
        setError(getApiErrorMessage(error, "Failed to load analysis."));

      } finally {
        setLoading(false);
      }

    },
    [datasetId]
  );



  useEffect(() => {

    loadAnalysis();

  }, [loadAnalysis]);



  return {

    data,

    loading,

    error,

    reload: loadAnalysis,

  };

}