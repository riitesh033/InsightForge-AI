import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import axios from "../../lib/axios";
import { toast } from "sonner";

const schema = z
  .object({
    new_password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type FormData = z.infer<typeof schema>;

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    if (!token) {
      toast.error("Invalid or missing reset token.");
      return;
    }
    setLoading(true);
    try {
      await axios.post("/auth/reset-password", {
        token,
        new_password: data.new_password,
      });
      toast.success("Password reset successful. Please log in.");
      navigate("/login");
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? "Failed to reset password.");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-600">Invalid or missing reset token.</p>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Reset Password</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <input
            type="password"
            placeholder="New password"
            {...register("new_password")}
            className="w-full border rounded px-3 py-2"
          />
          {errors.new_password && (
            <p className="text-red-600 text-sm">{errors.new_password.message}</p>
          )}
        </div>
        <div>
          <input
            type="password"
            placeholder="Confirm new password"
            {...register("confirm_password")}
            className="w-full border rounded px-3 py-2"
          />
          {errors.confirm_password && (
            <p className="text-red-600 text-sm">{errors.confirm_password.message}</p>
          )}
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded disabled:opacity-50"
        >
          {loading ? "Resetting..." : "Reset Password"}
        </button>
      </form>
    </div>
  );
}