import { useState, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [full_name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!full_name.trim()) {
      alert("Full name is required.");
      return;
    }

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
      await register(full_name, email, password);

      alert("Registration Successful!");

      navigate("/login");
    } catch (error: any) {
      console.error(error);

      alert(
        error.response?.data?.detail ??
        "Registration Failed"
      );
    }
  }

  return (
    <div className="mx-auto w-full max-w-md rounded-2xl border border-border bg-card p-8 shadow-xl">

      <h1 className="text-3xl font-bold text-foreground">
        Create Account
      </h1>

      <p className="mt-2 text-muted-foreground">
        Create your InsightForge AI account
      </p>

      <form
        onSubmit={handleSubmit}
        className="mt-8 space-y-5"
      >
        <div>
          <label className="text-sm font-medium text-foreground">
            Full Name
          </label>

          <input
            required
            type="text"
            value={full_name}
            onChange={(e) => setName(e.target.value)}
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
            placeholder="John Doe"
          />
        </div>

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
            placeholder="you@example.com"
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
            placeholder="Minimum 8 characters"
          />
        </div>

        <button
          type="submit"
          className="
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
          Register
        </button>
      </form>

      <div className="mt-6 text-center text-foreground">
        Already have an account?

        <Link
          to="/login"
          className="ml-2 text-primary hover:underline"
        >
          Login
        </Link>
      </div>

    </div>
  );
}