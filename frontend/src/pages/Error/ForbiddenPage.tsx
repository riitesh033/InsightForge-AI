import { Link } from "react-router-dom";
import { ShieldAlert } from "lucide-react";

export default function ForbiddenPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">

      <div className="max-w-lg text-center">

        <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-full bg-yellow-500/10">
          <ShieldAlert
            size={48}
            className="text-yellow-500"
          />
        </div>

        <h1 className="mt-8 text-6xl font-bold text-foreground">
          403
        </h1>

        <h2 className="mt-4 text-3xl font-semibold text-foreground">
          Access Denied
        </h2>

        <p className="mt-4 text-muted-foreground">
          You don't have permission to access this page.
        </p>

        <Link
          to="/dashboard"
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
          Go to Dashboard
        </Link>

      </div>

    </div>
  );
}