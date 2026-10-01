import { useEffect, useState, type FormEvent } from "react";
import { Eye, EyeOff, ShieldCheck } from "lucide-react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";
import { getApiErrorDetails } from "@/lib/api";

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
      <div className="flex min-h-screen items-center justify-center p-4">
        <p role="status" className="text-sm text-slate-600">
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
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-8 sm:px-6">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-xl sm:p-8">
        <div className="mb-6 flex items-center gap-3">
          <span className="flex size-11 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700">
            <ShieldCheck className="size-6" />
          </span>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">
              Admin Login
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              Sign in with an authorized administrator account.
            </p>
          </div>
        </div>

        {error && (
          <p
            role="alert"
            className="mb-5 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-800"
          >
            {error}
          </p>
        )}

        <form onSubmit={(event) => void handleSubmit(event)} className="space-y-5">
          <div>
            <label
              htmlFor="admin-email"
              className="text-sm font-medium text-slate-800"
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
              className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/20 disabled:opacity-60"
            />
          </div>

          <div>
            <label
              htmlFor="admin-password"
              className="text-sm font-medium text-slate-800"
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
                className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 pr-12 text-slate-900 outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/20 disabled:opacity-60"
              />
              <button
                type="button"
                onClick={() => setShowPassword((visible) => !visible)}
                disabled={submitting}
                aria-label={showPassword ? "Hide password" : "Show password"}
                aria-pressed={showPassword}
                className="absolute inset-y-0 right-2 flex items-center rounded-md px-2 text-slate-500 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-600"
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
            className="w-full rounded-lg bg-indigo-600 px-4 py-3 font-semibold text-white transition hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Signing in..." : "Login"}
          </button>
          {submitting && (
            <p role="status" className="text-center text-sm text-slate-600">
              Verifying administrator account...
            </p>
          )}
        </form>

        <p className="mt-6 text-center text-sm text-slate-600">
          Need a standard account?{" "}
          <Link
            to="/login"
            className="font-medium text-indigo-700 underline underline-offset-4"
          >
            User login
          </Link>
        </p>
      </section>
    </main>
  );
}
