import { useState } from "react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");

  return (
    <div className="mx-auto w-full max-w-md rounded-2xl border border-border bg-card p-8 shadow-xl">

      <h1 className="text-3xl font-bold text-foreground">
        Forgot Password
      </h1>

      <p className="mt-2 text-muted-foreground">
        Enter your email address and we'll send you a password reset link.
      </p>

      <div className="mt-8">

        <label className="text-sm font-medium text-foreground">
          Email Address
        </label>

        <input
          type="email"
          required
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

      </div>

      <button
        className="
          mt-6
          w-full
          rounded-lg
          bg-primary
          py-3
          font-semibold
          text-primary-foreground
          transition
          hover:opacity-90
        "
      >
        Send Reset Link
      </button>

    </div>
  );
}