interface Props {
  correlations?: Record<string, any>;
}


export default function CorrelationHeatmap({
  correlations,
}: Props) {

  if (!correlations) {
    return null;
  }


  const columns = Object.keys(correlations);


  return (
    <div className="rounded-2xl border bg-card p-6">

      <h2 className="text-xl font-semibold">
        Correlation Analysis
      </h2>

      <p className="mt-1 text-sm text-muted-foreground">
        Shows relationships between numerical columns.
      </p>


      <div className="mt-6 overflow-x-auto">

        <table className="w-full">

          <thead className="bg-muted/40">

            <tr>

              <th className="px-4 py-3 text-left">
                Column
              </th>

              {
                columns.map((column)=>(
                  <th
                    key={column}
                    className="px-4 py-3"
                  >
                    {column}
                  </th>
                ))
              }

            </tr>

          </thead>


          <tbody>

            {
              columns.map((row)=>(
                <tr
                  key={row}
                  className="border-t"
                >

                  <td className="px-4 py-3 font-medium">
                    {row}
                  </td>


                  {
                    columns.map((column)=>{

                      const value =
                        correlations[row]?.[column] ?? 0;


                      return (

                        <td
                          key={column}
                          className="px-4 py-3 text-center"
                        >

                          <span
                            className={
                              Number(value) > 0.7
                              ?
                              "rounded-lg bg-green-100 px-3 py-1 text-green-700 dark:bg-green-950 dark:text-green-400"
                              :
                              Number(value) < -0.7
                              ?
                              "rounded-lg bg-red-100 px-3 py-1 text-red-700 dark:bg-red-950 dark:text-red-400"
                              :
                              "rounded-lg bg-muted px-3 py-1"
                            }
                          >

                            {Number(value).toFixed(2)}

                          </span>


                        </td>

                      );

                    })
                  }


                </tr>
              ))
            }


          </tbody>

        </table>

      </div>


    </div>
  );
}