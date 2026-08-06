import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";


interface Props {
  missingValues: Record<string, number>;
}


export default function MissingValuesChart({
  missingValues,
}: Props) {


  const data = Object.entries(
    missingValues
  ).map(([name, value]) => ({
    name,
    missing: value,
  }));


  return (

    <div className="rounded-2xl border bg-card p-6">

      <h2 className="text-xl font-semibold">
        Missing Values Analysis
      </h2>


      <p className="mt-1 text-sm text-muted-foreground">
        Shows missing data count for each column.
      </p>


      <div className="mt-6 h-[300px]">

        {
          data.length === 0 ?

          (

            <div className="flex h-full items-center justify-center text-muted-foreground">

              No missing values detected.

            </div>

          )

          :

          (

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <BarChart data={data}>

                <XAxis
                  dataKey="name"
                />

                <YAxis />

                <Tooltip />

                <Bar
                  dataKey="missing"
                  radius={[6,6,0,0]}
                />

              </BarChart>

            </ResponsiveContainer>

          )

        }

      </div>

    </div>

  );

}