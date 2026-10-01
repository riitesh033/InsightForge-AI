import { useEffect, useState, type FormEvent } from "react";
import { Eye, EyeOff, ShieldCheck } from "lucide-react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";
import { getApiErrorDetails } from "@/lib/api";
import ThemeToggle from "@/components/common/ThemeToggle";

export default function AdminLoginPage() {
  const { loginAdmin, loading: authLoading, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && user?.is_superuser) {
      navigate("/admin", { replace: true });
    }
  }, [authLoading, navigate, user]);

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-4 text-foreground transition-colors duration-200">
        <p role="status"         className="text-sm text-muted-foreground">
          Checking your session...
        </p>
      </div>
    );
  }

  if (user?.is_superuser) {
    return <Navigate to="/admin" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const normalizedEmail = email.trim();
    if (!normalizedEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setError("Enter a valid email address.");
      return;
    }
    if (!password) {
      setError("Enter your password.");
      return;
    }

    setSubmitting(true);
    try {
      await loginAdmin(normalizedEmail, password);
      setPassword("");
      navigate("/admin", { replace: true });
    } catch (requestError) {
      const { status } = getApiErrorDetails(requestError);
      setError(
        status === 401
          ? "Unable to sign in with these credentials or this account is not authorized for admin access."
          : "Admin sign-in failed. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-8 text-foreground transition-colors duration-200 sm:px-6">
      <section className="w-full max-w-md rounded-2xl border border-border bg-card p-5 text-card-foreground shadow-xl transition-colors duration-200 sm:p-8">
        <div className="mb-6 flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
          <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <ShieldCheck className="size-6" />
          </span>
          <div>
            <h1 className="text-2xl font-bold text-foreground sm:text-3xl">
              Admin Login
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Sign in with an authorized administrator account.
            </p>
          </div>
          </div>
          <ThemeToggle />
        </div>

        {error && (
          <p
            role="alert"
            className="mb-5 rounded-lg border border-destructive/40 bg-destructive/5 px-3 py-2.5 text-sm text-destructive"
          >
            {error}
          </p>
        )}

        <form onSubmit={(event) => void handleSubmit(event)} className="space-y-5">
          <div>
            <label
              htmlFor="admin-email"
              className="text-sm font-medium text-foreground"
            >
              Email
            </label>
            <input
              id="admin-email"
              name="email"
              type="email"
              autoComplete="username"
              inputMode="email"
              required
              maxLength={255}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              disabled={submitting}
              className="mt-2 w-full rounded-lg border border-input bg-background px-4 py-3 text-foreground outline-none transition-colors duration-200 placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>

          <div>
            <label
              htmlFor="admin-password"
              className="text-sm font-medium text-foreground"
            >
              Password
            </label>
            <div className="relative mt-2">
              <input
                id="admin-password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={submitting}
                className="w-full rounded-lg border border-input bg-background px-4 py-3 pr-12 text-foreground outline-none transition-colors duration-200 placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
              />
              <button
                type="button"
                onClick={() => setShowPassword((visible) => !visible)}
                disabled={submitting}
                aria-label={showPassword ? "Hide password" : "Show password"}
                aria-pressed={showPassword}
                className="absolute inset-y-0 right-2 flex items-center rounded-md px-2 text-muted-foreground transition-colors duration-200 hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
              >
                {showPassword ? (
                  <EyeOff className="size-5" aria-hidden="true" />
                ) : (
                  <Eye className="size-5" aria-hidden="true" />
                )}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-primary px-4 py-3 font-semibold text-primary-foreground transition-colors duration-200 hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Signing in..." : "Login"}
          </button>
          {submitting && (
            <p role="status" className="text-center text-sm text-muted-foreground">
              Verifying administrator account...
            </p>
          )}
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Need a standard account?{" "}
          <Link
            to="/login"
            className="font-medium text-primary underline underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            User login
          </Link>
        </p>
      </section>
    </main>
  );
}
