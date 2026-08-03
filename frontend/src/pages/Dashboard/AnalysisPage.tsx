import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { getAnalysis } from "@/services/analysis";

export default function AnalysisPage() {
  const { datasetId } = useParams();

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const load = async () => {
      console.log("datasetId =", datasetId);

      try {
        const result = await getAnalysis(Number(datasetId));

        console.log("API Response:", result);

        setData(result);
      } catch (err) {
        console.error("API Error:", err);
      }

      console.log("Setting loading = false");
      setLoading(false);
    };

    load();
  }, [datasetId]);

  if (loading) {
    return <h1>Loading...</h1>;
  }

  return (
    <pre style={{ color: "white" }}>
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}