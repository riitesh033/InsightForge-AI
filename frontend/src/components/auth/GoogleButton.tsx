import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { getApiErrorMessage } from "@/lib/api";
import { showError } from "@/lib/toast";

export default function GoogleButton() {
  const { loginWithGoogle } = useAuth();
  const [loading, setLoading] = useState(false);

  async function handleGoogleLogin() {
    setLoading(true);
    try {
      await loginWithGoogle();
    } catch (error) {
      showError(
        getApiErrorMessage(error, "Google sign-in is currently unavailable.")
      );
      setLoading(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleGoogleLogin}
      disabled={loading}
      className="mt-5 w-full rounded-lg border border-border bg-background py-3 font-semibold text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-60"
    >
      {loading ? "Connecting to Google..." : "Continue with Google"}
    </button>
  );
}
