import {
  Sparkles,
} from "lucide-react";


interface Props {
  summary: string;
}


export default function AIInsights({
  summary,
}: Props) {


  return (

    <div className="rounded-2xl border bg-card p-6">


      <div className="flex items-center gap-3">


        <div className="rounded-xl bg-primary/10 p-3">

          <Sparkles
            className="h-6 w-6 text-primary"
          />

        </div>


        <div>

          <h2 className="text-xl font-semibold">
            AI Generated Insights
          </h2>

          <p className="text-sm text-muted-foreground">
            Automated analysis generated from your dataset.
          </p>

        </div>


      </div>



      <div className="mt-6 rounded-xl bg-muted/40 p-5">

        <p className="leading-relaxed">
          {
            summary ||
            "No AI insights available."
          }
        </p>


      </div>


    </div>

  );

}