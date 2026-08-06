import {
  useParams,
} from "react-router-dom";

import {
  useAnalysis,
} from "@/hooks/useAnalysis";


export default function AnalysisPage() {

  const {
    datasetId,
  } = useParams();


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
      <div className="text-red-500">
        {error}
      </div>
    );

  }


  if (!data) {

    return (
      <div>
        No analysis found.
      </div>
    );

  }



  return (

    <div className="space-y-8">


      <div>

        <h1 className="text-3xl font-bold">
          Analysis Report
        </h1>


        <p className="text-muted-foreground">
          Dataset ID: {data.dataset_id}
        </p>

      </div>



      <div className="rounded-2xl border bg-card p-6">

        <h2 className="text-xl font-semibold">
          Data Quality Score
        </h2>


        <div className="mt-4 text-5xl font-bold text-primary">

          {data.quality_score}%

        </div>

      </div>



      <div className="rounded-2xl border bg-card p-6">

        <h2 className="text-xl font-semibold">
          AI Summary
        </h2>


        <p className="mt-3 text-muted-foreground">

          {data.summary_text}

        </p>


      </div>



    </div>

  );

}