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


        console.log(
          "Fetching analysis for dataset:",
          datasetId
        );


        const response =
          await getAnalysis(
            Number(datasetId)
          );


        console.log(
          "Analysis response:",
          response
        );


        setData(response);


      } catch (error: any) {


        console.error(
          "Analysis API error:",
          error?.response?.data || error
        );


        setData(null);


        setError(
          error?.response?.data?.detail ||
          "Failed to load analysis."
        );


      } finally {


        setLoading(false);


        console.log(
          "Analysis loading finished"
        );

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