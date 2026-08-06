interface Props {
  columnInfo: Record<string, any>;
  statistics: Record<string, any>;
}


export default function ColumnInfoTable({
  columnInfo,
  statistics,
}: Props) {


  const columns = Object.keys(columnInfo);



  return (

    <div className="rounded-2xl border bg-card shadow-sm">

      <div className="border-b p-6">

        <h2 className="text-xl font-semibold">
          Column Information
        </h2>

        <p className="mt-1 text-sm text-muted-foreground">
          Detailed information about every dataset column.
        </p>

      </div>



      <div className="overflow-x-auto">


        <table className="w-full">


          <thead className="bg-muted/40">

            <tr>

              <th className="px-5 py-3 text-left">
                Column
              </th>


              <th className="px-5 py-3 text-left">
                Data Type
              </th>


              <th className="px-5 py-3 text-center">
                Unique
              </th>


              <th className="px-5 py-3 text-center">
                Missing
              </th>


              <th className="px-5 py-3 text-center">
                Mean
              </th>


              <th className="px-5 py-3 text-center">
                Std
              </th>


            </tr>

          </thead>



          <tbody>


            {
              columns.length === 0 ?

              (

                <tr>

                  <td
                    colSpan={6}
                    className="py-10 text-center text-muted-foreground"
                  >

                    No column information available.

                  </td>

                </tr>

              )


              :

              columns.map((column)=>{


                const info =
                  columnInfo[column] ?? {};


                const stats =
                  statistics[column] ?? {};



                return (

                  <tr
                    key={column}
                    className="border-t hover:bg-muted/30"
                  >


                    <td className="px-5 py-4 font-medium">
                      {column}
                    </td>


                    <td className="px-5 py-4">
                      {info.dtype ?? "-"}
                    </td>


                    <td className="px-5 py-4 text-center">
                      {info.unique ?? "-"}
                    </td>


                    <td className="px-5 py-4 text-center">
                      {info.missing ?? 0}
                    </td>


                    <td className="px-5 py-4 text-center">
                      {
                        typeof stats.mean === "number"
                        ?
                        stats.mean.toFixed(2)
                        :
                        "-"
                      }
                    </td>


                    <td className="px-5 py-4 text-center">
                      {
                        typeof stats.std === "number"
                        ?
                        stats.std.toFixed(2)
                        :
                        "-"
                      }
                    </td>


                  </tr>

                );

              })

            }


          </tbody>


        </table>

      </div>


    </div>

  );

}