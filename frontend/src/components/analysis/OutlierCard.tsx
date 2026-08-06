import {
  AlertTriangle,
} from "lucide-react";


interface Props {
  outliers?: Record<string, any>;
}


export default function OutlierCard({
  outliers,
}: Props) {


  if (!outliers) {
    return null;
  }


  const columns =
    Object.keys(outliers);



  return (

    <div className="rounded-2xl border bg-card p-6">


      <div className="flex items-center gap-3">

        <div className="rounded-xl bg-red-100 p-3 dark:bg-red-950">

          <AlertTriangle
            className="h-6 w-6 text-red-600"
          />

        </div>


        <div>

          <h2 className="text-xl font-semibold">
            Outlier Detection
          </h2>


          <p className="text-sm text-muted-foreground">
            Abnormal values detected in columns.
          </p>

        </div>


      </div>



      <div className="mt-6 space-y-3">

        {
          columns.length === 0 ?

          (
            <p className="text-muted-foreground">
              No outliers detected.
            </p>
          )

          :

          columns.map((column)=>(

            <div
              key={column}
              className="flex justify-between rounded-xl border p-4"
            >

              <span>
                {column}
              </span>


              <span className="font-semibold">

                {outliers[column]}

              </span>


            </div>

          ))

        }

      </div>


    </div>

  );

}