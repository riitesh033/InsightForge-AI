import { useCallback, useEffect, useState } from "react";

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


      try {

        setLoading(true);
        setError("");

        const response =
          await getAnalysis(
            Number(datasetId)
          );

        setData(response);

      } catch (error) {
        setData(null);

        setError(
          error instanceof Error && 'response' in error 
            ? (error as any).response?.data?.detail || "Failed to load analysis."
            : error instanceof Error 
              ? error.message 
              : "Failed to load analysis."
        );

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