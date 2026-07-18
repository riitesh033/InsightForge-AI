import { useState, FormEvent } from "react";

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

      // TODO:
      // await forgotPassword(email);

      // Simulate API request
      await new Promise((resolve) => setTimeout(resolve, 1500));

      showSuccess(
        "Password reset link has been sent to your email."
      );

      setEmail("");

    } catch (error: any) {
      console.error(error);

      showError(
        error?.response?.data?.detail ??
        "Failed to send reset link."
      );

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

        <label className="text-sm font-medium text-foreground">
          Email Address
        </label>

        <input
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