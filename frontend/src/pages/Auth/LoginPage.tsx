import { useState, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";

import { useAuth } from "@/hooks/useAuth";
import { showSuccess, showError } from "@/lib/toast";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
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

    if (!password.trim()) {
      showError("Password is required.");
      return;
    }

    if (password.length < 8) {
      showError("Password must be at least 8 characters.");
      return;
    }

    try {
      setLoading(true);

      await login(email, password);

      showSuccess("Welcome back!");

      navigate("/dashboard");

    } catch (error: any) {
      console.error(error);

      showError(
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
            placeholder="Enter your email"
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

          <div className="relative mt-2">
            <input
              required
              type={showPassword ? "text" : "password"}
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="
                w-full
                rounded-lg
                border
                border-border
                bg-background
                px-4
                py-3
                pr-12
                text-foreground
                placeholder:text-muted-foreground
                focus:border-primary
                focus:outline-none
                focus:ring-2
                focus:ring-primary/20
              "
            />

            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="
                absolute
                right-3
                top-1/2
                -translate-y-1/2
                text-muted-foreground
                transition-colors
                hover:text-foreground
                focus:outline-none
              "
              aria-label={
                showPassword ? "Hide password" : "Show password"
              }
            >
              {showPassword ? (
                <EyeOff size={20} />
              ) : (
                <Eye size={20} />
              )}
            </button>
          </div>
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
            transition-all
            duration-200
            hover:opacity-90
            hover:shadow-lg
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

