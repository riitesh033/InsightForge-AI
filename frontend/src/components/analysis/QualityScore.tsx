interface Props {
  score: number;
}


export default function QualityScore({
  score,
}: Props) {


  return (

    <div className="rounded-2xl border bg-card p-6">

      <h2 className="text-xl font-semibold">
        Data Quality Score
      </h2>


      <div className="mt-6 flex items-center gap-6">


        <div
          className="flex h-32 w-32 items-center justify-center rounded-full border-8"
        >

          <span className="text-3xl font-bold">
            {score}%
          </span>

        </div>


        <div>

          {
            score >= 80 ?

            <p className="text-green-600">
              Excellent dataset quality
            </p>

            :

            score >= 50 ?

            <p className="text-yellow-600">
              Dataset needs cleaning
            </p>

            :

            <p className="text-red-600">
              Poor dataset quality
            </p>

          }

        </div>


      </div>


    </div>

  );

}