import {
  CheckCircle2,
  Copy,
  AlertTriangle,
} from "lucide-react";

interface DuplicateInfo {
  count: number;
  has_duplicates?: boolean;
  percent?: number;
}

interface Props {
  duplicates: DuplicateInfo;
}

export default function DuplicateCard({
  duplicates,
}: Props) {
  const count = duplicates?.count ?? 0;

  const percent = duplicates?.percent ?? 0;

  const hasDuplicates =
    duplicates?.has_duplicates ?? count > 0;

  return (
    <div className="rounded-2xl border bg-card p-6 shadow-sm">

      {/* Header */}
      <div className="flex items-start justify-between">

        <div className="flex items-center gap-4">

          <div
            className={`rounded-xl p-3 ${
              hasDuplicates
                ? "bg-orange-500/10"
                : "bg-green-500/10"
            }`}
          >
            {hasDuplicates ? (
              <AlertTriangle className="h-6 w-6 text-orange-500" />
            ) : (
              <CheckCircle2 className="h-6 w-6 text-green-500" />
            )}
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

        <Copy className="h-5 w-5 text-muted-foreground" />

      </div>

      {/* Percentage */}
      {percent > 0 && (
        <div className="mt-5">

          <div className="mb-2 flex justify-between text-sm">

            <span className="text-muted-foreground">
              Duplicate percentage
            </span>

            <span className="font-medium">
              {percent.toFixed(2)}%
            </span>

          </div>

          <div className="h-2 overflow-hidden rounded-full bg-muted">

            <div
              className="h-full rounded-full bg-orange-500 transition-all"
              style={{
                width: `${Math.min(percent, 100)}%`,
              }}
            />

          </div>

        </div>
      )}

      {/* Status */}
      <div className="mt-5">

        {hasDuplicates ? (
          <p className="text-sm text-orange-600 dark:text-orange-400">
            Dataset contains duplicate records that may
            require cleaning.
          </p>
        ) : (
          <p className="text-sm text-green-600 dark:text-green-400">
            No duplicate rows found. Your dataset is clean
            in this area.
          </p>
        )}

      </div>

    </div>
  );
}