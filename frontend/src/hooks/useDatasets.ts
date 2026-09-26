import { useCallback, useEffect, useState } from "react";

import {
  DatasetListResponse,
  getDatasets,
} from "@/services/dataset";

export function useDatasets() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [data, setData] =
    useState<DatasetListResponse | null>(null);

  const [search, setSearch] = useState("");

  const loadDatasets = useCallback(async () => {
    try {
      setLoading(true);

      const result = await getDatasets({
        search,
      });

      setData(result);
      setError("");
    } catch {
      setError("Failed to load datasets.");
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      loadDatasets();
    }, 400);

    return () => clearTimeout(timeout);
  }, [loadDatasets]);

  return {
    loading,
    error,
    data,
    reload: loadDatasets,
    search,
    setSearch,
  };
}