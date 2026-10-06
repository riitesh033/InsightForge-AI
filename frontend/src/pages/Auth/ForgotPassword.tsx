import { useState, FormEvent } from "react";

import { forgotPassword } from "@/services/auth";
import { showSuccess, showError } from "@/lib/toast";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!email.trim()) {
      showError("Email is required.");
      return;
    }

    if (!emailRegex.test(email)) {
      showError("Please enter a valid email address.");
      return;
    }

    try {
      setLoading(true);

      // Call the real backend password reset endpoint.
      // The API returns the same generic message whether or not the
      // account exists (no account enumeration).
      const result = await forgotPassword(email);

      showSuccess(result.message);

      setEmail("");

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Failed to send reset link";
      
      showError(errorMessage);

    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-md rounded-2xl border border-border bg-card p-8 shadow-xl">

      <h1 className="text-3xl font-bold text-foreground">
        Forgot Password
      </h1>

      <p className="mt-2 text-muted-foreground">
        Enter your email address and we'll send you a password reset link.
      </p>

      <form
        onSubmit={handleSubmit}
        className="mt-8"
      >

        <label
          htmlFor="forgot-password-email"
          className="text-sm font-medium text-foreground"
        >
          Email Address
        </label>

        <input
          id="forgot-password-email"
          required
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          className="
            mt-2
            w-full
            rounded-lg
            border
            border-border
            bg-background
            px-4
            py-3
            text-foreground
            placeholder:text-muted-foreground
            focus:border-primary
            focus:outline-none
            focus:ring-2
            focus:ring-primary/20
          "
        />

        <button
          type="submit"
          disabled={loading}
          className="
            mt-6
            w-full
            rounded-lg
            bg-primary
            py-3
            font-semibold
            text-primary-foreground
            transition-all
            duration-200
            hover:opacity-90
            hover:shadow-lg
            disabled:cursor-not-allowed
            disabled:opacity-60
          "
        >
          {loading ? "Sending..." : "Send Reset Link"}
        </button>

      </form>

    </div>
  );
}