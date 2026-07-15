import { useState } from "react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");

  return (
    <div className="mx-auto w-full max-w-md rounded-2xl bg-white p-8 shadow-xl dark:bg-slate-900">

      <h1 className="text-3xl font-bold">
        Forgot Password
      </h1>

      <p className="mt-2 text-slate-500">
        Enter your email address.
      </p>

      <input
        className="mt-8 w-full rounded-lg border p-3"
        value={email}
        onChange={(e)=>setEmail(e.target.value)}
        placeholder="Email"
      />

      <button
        className="mt-6 w-full rounded-lg bg-indigo-600 p-3 text-white"
      >
        Send Reset Link
      </button>

    </div>
  );
}