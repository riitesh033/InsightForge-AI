import { Link } from "react-router-dom";
import { SearchX } from "lucide-react";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">

      <div className="max-w-lg text-center">

        <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-full bg-primary/10">
          <SearchX
            size={48}
            className="text-primary"
          />
        </div>

        <h1 className="mt-8 text-6xl font-bold text-foreground">
          404
        </h1>

        <h2 className="mt-4 text-3xl font-semibold text-foreground">
          Page Not Found
        </h2>

        <p className="mt-4 text-muted-foreground">
          The page you are looking for doesn't exist or has been moved.
        </p>

        <Link
          to="/"
          className="
            mt-8
            inline-flex
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
          Back to Home
        </Link>

      </div>

    </div>
  );
}