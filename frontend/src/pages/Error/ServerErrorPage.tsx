import { RotateCcw, TriangleAlert } from "lucide-react";

export default function ServerErrorPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">

      <div className="max-w-lg text-center">

        <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-full bg-red-500/10">
          <TriangleAlert
            size={48}
            className="text-red-500"
          />
        </div>

        <h1 className="mt-8 text-6xl font-bold text-foreground">
          500
        </h1>

        <h2 className="mt-4 text-3xl font-semibold text-foreground">
          Internal Server Error
        </h2>

        <p className="mt-4 text-muted-foreground">
          Something went wrong while processing your request.
        </p>

        <button
          onClick={() => window.location.reload()}
          className="
            mt-8
            inline-flex
            items-center
            gap-2
            rounded-lg
            bg-primary
            px-6
            py-3
            font-semibold
            text-primary-foreground
            transition
            hover:opacity-90
          "
        >
          <RotateCcw size={18} />
          Try Again
        </button>

      </div>

    </div>
  );
}