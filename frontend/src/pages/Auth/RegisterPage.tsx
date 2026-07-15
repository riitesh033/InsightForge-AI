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
    await register(
      full_name,
      email,
      password
    );

    alert("Registration Successful!");

    navigate("/login");

  } catch (error: any) {
    console.error(error);

    alert(
      error.response?.data?.detail ??
      "Registration failed."
    );
  }
}

  return (
    <div className="mx-auto w-full max-w-md rounded-2xl bg-white p-8 shadow-xl dark:bg-slate-900">

      <h1 className="text-3xl font-bold">
        Create Account
      </h1>

      <form
        onSubmit={handleSubmit}
        className="mt-8 space-y-5"
      >
        <input
          className="w-full rounded-lg border p-3"
          placeholder="Full Name"
          value={full_name}
          onChange={(e)=>setName(e.target.value)}
        />

        <input
          className="w-full rounded-lg border p-3"
          placeholder="Email"
          type="email"
          value={email}
          onChange={(e)=>setEmail(e.target.value)}
        />

        <input
          className="w-full rounded-lg border p-3"
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e)=>setPassword(e.target.value)}
        />

        <button className="w-full rounded-lg bg-indigo-600 p-3 text-white">
          Register
        </button>

      </form>

      <div className="mt-6 text-center">

        Already have an account?

        <Link
          to="/login"
          className="ml-2 text-indigo-600"
        >
          Login
        </Link>

      </div>

    </div>
  );
}