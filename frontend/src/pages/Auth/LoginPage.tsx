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
    <div className="mx-auto w-full max-w-md rounded-2xl border border-border bg-card p-8 shadow-xl">

      <h1 className="text-3xl font-bold text-foreground">
        Welcome Back
      </h1>

      <p className="mt-2 text-muted-foreground">
        Login to your account
      </p>

      <form
        onSubmit={handleSubmit}
        className="mt-8 space-y-5"
      >
        <div>
          <label className="text-sm font-medium text-foreground">
            Email
          </label>

          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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

        <div>
          <label className="text-sm font-medium text-foreground">
            Password
          </label>

          <input
            required
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
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
          type="submit"
          disabled={loading}
          className="
            w-full
            rounded-lg
            bg-primary
            py-3
            font-semibold
            text-primary-foreground
            transition
            hover:opacity-90
            disabled:cursor-not-allowed
            disabled:opacity-60
          "
        >
          {loading ? "Signing In..." : "Login"}
        </button>
      </form>

      <div className="mt-6 text-center">
        <Link
          to="/forgot-password"
          className="text-primary hover:underline"
        >
          Forgot Password?
        </Link>
      </div>

      <div className="mt-3 text-center text-foreground">
        Don't have an account?

        <Link
          to="/register"
          className="ml-2 text-primary hover:underline"
        >
          Register
        </Link>
      </div>

    </div>
  );
}