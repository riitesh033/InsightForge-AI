import { useState, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const navigate = useNavigate();

  const { login } = useAuth();

  const [email, setEmail] = useState("");

  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);

 async function handleSubmit(e: FormEvent) {
  e.preventDefault();

  // Email Validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!email.trim()) {
    alert("Email is required.");
    return;
  }

  if (!emailRegex.test(email)) {
    alert("Please enter a valid email address.");
    return;
  }

  if (!password.trim()) {
    alert("Password is required.");
    return;
  }

  if (password.length < 8) {
    alert("Password must be at least 8 characters.");
    return;
  }

  try {
    setLoading(true);

    await login(email, password);

    navigate("/dashboard");

  } catch (error: any) {
    console.error(error);

    alert(
      error.response?.data?.detail ??
      "Invalid email or password."
    );

  } finally {
    setLoading(false);
  }
}

  return (
    <div className="mx-auto w-full max-w-md rounded-2xl bg-white p-8 shadow-xl dark:bg-slate-900">

      <h1 className="text-3xl font-bold">
        Welcome Back
      </h1>

      <p className="mt-2 text-slate-500">
        Login to your account
      </p>

      <form
        onSubmit={handleSubmit}
        className="mt-8 space-y-5"
      >
        <div>

          <label>Email</label>

          <input
            className="mt-2 w-full rounded-lg border p-3"
            type="email"
            value={email}
            onChange={(e)=>setEmail(e.target.value)}
          />

        </div>

        <div>

          <label>Password</label>

          <input
            className="mt-2 w-full rounded-lg border p-3"
            type="password"
            value={password}
            onChange={(e)=>setPassword(e.target.value)}
          />

        </div>

        <button
          className="w-full rounded-lg bg-indigo-600 p-3 font-semibold text-white"
          disabled={loading}
        >
          {loading ? "Signing In..." : "Login"}
        </button>
      </form>

      <div className="mt-6 text-center">

        <Link
          to="/forgot-password"
          className="text-indigo-600"
        >
          Forgot Password?
        </Link>

      </div>

      <div className="mt-3 text-center">

        Don't have an account?

        <Link
          className="ml-2 text-indigo-600"
          to="/register"
        >
          Register
        </Link>

      </div>

    </div>
  );
}