import {
  Copy,
} from "lucide-react";


interface Props {
  duplicates: Record<string, any>;
}


export default function DuplicateCard({
  duplicates,
}: Props) {


  const count =
    duplicates.count ?? 0;



  return (

    <div className="rounded-2xl border bg-card p-6">


      <div className="flex items-center gap-4">


        <div className="rounded-xl bg-primary/10 p-3">

          <Copy
            className="h-6 w-6 text-primary"
          />

        </div>



        <div>

          <p className="text-sm text-muted-foreground">
            Duplicate Records
          </p>


          <h2 className="text-3xl font-bold">
            {count}
          </h2>


        </div>


      </div>



      <p className="mt-4 text-sm text-muted-foreground">

        {
          count === 0
          ?
          "No duplicate rows found."
          :
          "Dataset contains duplicate records that may require cleaning."
        }

      </p>


    </div>

  );

}